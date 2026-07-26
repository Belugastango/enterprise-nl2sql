import re
import time
import pandas as pd
from sqlalchemy import create_engine, inspect, text, MetaData
from typing import Dict, Any, Tuple, Optional

class DatabaseManager:
    """Manages database connectivity, schema inspection, security validation, and query execution."""

    FORBIDDEN_KEYWORDS = [
        r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b', r'\bALTER\b',
        r'\bTRUNCATE\b', r'\bGRANT\b', r'\bREVOKE\b', r'\bCREATE\b', r'\bREPLACE\b',
        r'\bEXEC\b', r'\bEXECUTE\b', r'\bPRAGMA\b', r'\bVACUUM\b'
    ]

    def __init__(self, db_type: str = "sqlite", db_path: str = "sample_company.db", pg_config: Optional[Dict[str, Any]] = None):
        self.db_type = db_type.lower()
        self.db_path = db_path
        self.pg_config = pg_config or {}
        self.engine = self._create_engine()

    def _create_engine(self):
        if self.db_type == "sqlite":
            return create_engine(f"sqlite:///{self.db_path}")
        elif self.db_type == "postgresql":
            host = self.pg_config.get("host", "localhost")
            port = self.pg_config.get("port", 5432)
            dbname = self.pg_config.get("dbname", "postgres")
            user = self.pg_config.get("user", "postgres")
            password = self.pg_config.get("password", "")
            import urllib.parse
            encoded_password = urllib.parse.quote_plus(password)
            uri = f"postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}"
            return create_engine(uri)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def test_connection(self) -> Tuple[bool, str]:
        """Verifies connection to the database."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    def validate_sql_safety(self, sql: str, is_admin: bool = False) -> Tuple[bool, str]:
        """Validates that the SQL query is safe to execute based on mode."""
        clean_sql = re.sub(r'--.*?\n|/\*.*?\*/', '', sql, flags=re.DOTALL).strip()
        
        # Check for multiple statements separated by semicolon (unless last char)
        statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
        if len(statements) > 1 and not is_admin:
            return False, "Security Error: Multiple SQL statements are not allowed in Analyst mode."

        upper_sql = clean_sql.upper()
        if not is_admin:
            # Check for forbidden mutation keywords
            for kw in self.FORBIDDEN_KEYWORDS:
                if re.search(kw, upper_sql):
                    return False, f"Security Error: Prohibited operation detected ({kw.replace(r'\b', '')}). Only SELECT queries are permitted in Analyst mode."

            if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
                return False, "Security Error: Query must start with SELECT or WITH (CTE)."

        return True, "Query passed security validation."

    def get_schema_summary(self) -> str:
        """Inspects database schema and returns structured Markdown for LLM prompt context."""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
        except Exception as e:
            return f"❌ Unable to connect to {self.db_type.upper()} database schema: {str(e)}"
        
        schema_md = f"### Database Dialect: {self.db_type.upper()}\n\n"
        
        for table_name in tables:
            try:
                columns = inspector.get_columns(table_name)
                pks = inspector.get_pk_constraint(table_name).get('constrained_columns', [])
                fks = inspector.get_foreign_keys(table_name)
                
                fk_map = {}
                for fk in fks:
                    for local_col, ref_col in zip(fk['constrained_columns'], fk['referred_columns']):
                        fk_map[local_col] = f"{fk['referred_table']}.{ref_col}"

                schema_md += f"#### Table: `{table_name}`\n"
                schema_md += "| Column | Type | Attributes |\n"
                schema_md += "| --- | --- | --- |\n"
                
                for col in columns:
                    col_name = col['name']
                    col_type = str(col['type'])
                    attrs = []
                    if col_name in pks:
                        attrs.append("PRIMARY KEY")
                    if col_name in fk_map:
                        attrs.append(f"FOREIGN KEY -> {fk_map[col_name]}")
                    if not col.get('nullable', True):
                        attrs.append("NOT NULL")
                    
                    attr_str = ", ".join(attrs) if attrs else "None"
                    schema_md += f"| `{col_name}` | `{col_type}` | {attr_str} |\n"
                
                # Fetch sample rows for context
                try:
                    with self.engine.connect() as conn:
                        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 2"))
                        sample_rows = [dict(row._mapping) for row in result]
                        if sample_rows:
                            schema_md += f"**Sample Data ({table_name})**:\n```json\n{sample_rows}\n```\n"
                except Exception:
                    pass
                    
                schema_md += "\n---\n"
            except Exception as te:
                schema_md += f"Could not inspect table `{table_name}`: {str(te)}\n\n"
            
        return schema_md

    def get_schema_details(self) -> Dict[str, pd.DataFrame]:
        """Returns DataFrames of columns and sample rows per table for UI Schema Explorer."""
        details = {}
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
        except Exception:
            return details
        
        for table in tables:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 10", self.engine)
                details[table] = df
            except Exception:
                details[table] = pd.DataFrame()
        return details

    def execute_query(self, sql: str, max_rows: int = 500, is_admin: bool = False) -> Tuple[Optional[pd.DataFrame], float, Optional[str]]:
        """Safely executes SQL query and returns DataFrame, execution time, and error string if any."""
        is_safe, msg = self.validate_sql_safety(sql, is_admin)
        if not is_safe:
            return None, 0.0, msg

        clean_sql = sql.strip().rstrip(';')
        upper_sql = clean_sql.upper()
        is_select = upper_sql.startswith("SELECT") or upper_sql.startswith("WITH") or upper_sql.startswith("SHOW")
        
        # Inject LIMIT if not present and query is simple SELECT
        if is_select and not re.search(r'\bLIMIT\b', clean_sql, re.IGNORECASE) and not re.search(r'\bOFFSET\b', clean_sql, re.IGNORECASE):
            clean_sql += f" LIMIT {max_rows}"

        start_time = time.time()
        try:
            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                if is_select:
                    df = pd.read_sql_query(text(clean_sql), conn)
                else:
                    conn.execute(text(clean_sql))
                    df = pd.DataFrame({"Status": ["Success"], "Action": [f"Executed {upper_sql.split()[0]} successfully"]})
            elapsed = time.time() - start_time
            return df, elapsed, None
        except Exception as e:
            elapsed = time.time() - start_time
            return None, elapsed, str(e)

    def get_table_schema_df(self, table_name: str) -> pd.DataFrame:
        """Returns a DataFrame of [Column Name, Data Type] for the visual editor."""
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            if table_name not in inspector.get_table_names():
                return pd.DataFrame(columns=["Column Name", "Data Type"])
            columns = inspector.get_columns(table_name)
            data = [{"Column Name": col["name"], "Data Type": str(col["type"])} for col in columns]
            return pd.DataFrame(data)
        except Exception as e:
            import pandas as pd
            return pd.DataFrame(columns=["Column Name", "Data Type"])

    def import_csv_to_table(self, file_obj, table_name: str, if_exists: str = "fail") -> Tuple[bool, str]:
        """Reads a CSV file and imports it into the database as a table."""
        try:
            import pandas as pd
            import re
            
            df = pd.read_csv(file_obj)
            
            # Clean column names for SQL safety
            clean_cols = []
            for col in df.columns:
                c = str(col).strip().lower()
                c = re.sub(r'[^a-z0-9_]', '_', c)
                c = re.sub(r'_+', '_', c).strip('_')
                if not c:
                    c = "col"
                if c[0].isdigit():
                    c = "c_" + c
                clean_cols.append(c)
            df.columns = clean_cols
            
            # Clean table name
            clean_table = str(table_name).strip().lower()
            clean_table = re.sub(r'[^a-z0-9_]', '_', clean_table)
            clean_table = re.sub(r'_+', '_', clean_table).strip('_')
            if not clean_table or clean_table[0].isdigit():
                return False, "Invalid table name. Must start with a letter and contain only alphanumeric characters and underscores."

            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                df.to_sql(name=clean_table, con=conn, if_exists=if_exists, index=False)
            
            return True, f"Successfully imported {len(df)} rows into table '{clean_table}'."
        except Exception as e:
            return False, f"CSV Import failed: {str(e)}"
