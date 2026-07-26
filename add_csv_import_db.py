import os

db_mgr_file = '/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/db_manager.py'
with open(db_mgr_file, 'r') as f:
    db_content = f.read()

if "def import_csv_to_table" not in db_content:
    new_method = '''
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
'''
    with open(db_mgr_file, 'a') as f:
        f.write(new_method)
    print("Added import_csv_to_table to db_manager.py")
