# Script to append to db_manager and ai_engine
import os

db_mgr_file = '/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/db_manager.py'
with open(db_mgr_file, 'r') as f:
    db_content = f.read()

if "def get_table_schema_df" not in db_content:
    new_method = '''
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
'''
    with open(db_mgr_file, 'a') as f:
        f.write(new_method)
    print("Added get_table_schema_df to db_manager.py")

ai_engine_file = '/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/ai_engine.py'
with open(ai_engine_file, 'r') as f:
    ai_content = f.read()

if "def generate_schema_migration_sql" not in ai_content:
    ai_new_method = '''
    def generate_schema_migration_sql(self, table_name: str, old_schema: str, new_schema: str, dialect: str) -> str:
        """Uses Gemini to generate ALTER TABLE statements from visual schema edits."""
        if not self.is_configured():
            raise ValueError("Gemini API Key is missing.")

        system_instruction = f"""
You are an expert Database Migration AI.
Your task is to generate the exact {dialect.upper()} SQL queries needed to migrate a table from its Old Schema to its New Schema.
Return ONLY the raw SQL queries, separated by semicolons if there are multiple. Do not include markdown formatting or explanations.
Be aware of {dialect.upper()} specific syntax for adding, dropping, or renaming columns, and changing data types.
"""
        prompt = f"""
Table Name: {table_name}

Old Schema:
{old_schema}

New Schema:
{new_schema}

Generate the {dialect.upper()} SQL to perform this migration.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0
                )
            )
            return self._extract_sql_from_text(response.text or "")
        except Exception as e:
            raise RuntimeError(f"Schema Migration AI Error: {str(e)}")
'''
    with open(ai_engine_file, 'a') as f:
        f.write(ai_new_method)
    print("Added generate_schema_migration_sql to ai_engine.py")
