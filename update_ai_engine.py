with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/ai_engine.py', 'r') as f:
    content = f.read()

old_gen = '''    def generate_sql(self, user_question: str, schema_info: str, dialect: str = "sqlite") -> str:
        """Translates plain English question into dialect-specific SQL query."""
        if not self.is_configured():
            raise ValueError("Gemini API Key is not configured. Please enter your API key in the sidebar.")

        system_instruction = f"""
You are an expert Enterprise SQL Data Analyst.
Your task is to convert a user's natural language business question into an accurate, efficient, read-only SQL query for a {dialect.upper()} database.

Database Schema & Dialect Context:
{schema_info}

CRITICAL INSTRUCTIONS:
1. Return ONLY the raw SQL query. Do NOT add markdown intros, explanations, or commentary outside the query block.
2. Dialect Specific Rules ({dialect.upper()}):
   - For SQLite: Use strftime('%Y', column), strftime('%m', column), datetime functions, or LIKE for dates.
   - For PostgreSQL: Use DATE_TRUNC('month', column), EXTRACT(YEAR FROM column), or standard Postgres date operators.
3. Handle Quarter Queries:
   - Q1: Month 01-03
   - Q2: Month 04-06
   - Q3: Month 07-09
   - Q4: Month 10-12
4. Security: Generate STRICTLY read-only SELECT or WITH (CTE) statements. Never generate INSERT, UPDATE, DELETE, DROP, or ALTER commands.
5. Use clear column aliases so chart labels and metric columns look clean.
"""'''

new_gen = '''    def generate_sql(self, user_question: str, schema_info: str, dialect: str = "sqlite", is_admin: bool = False) -> str:
        """Translates plain English question into dialect-specific SQL query."""
        if not self.is_configured():
            raise ValueError("Gemini API Key is not configured. Please enter your API key in the sidebar.")

        if is_admin:
            role = "Expert Database Administrator"
            security_rule = "Security: You are in ADMIN MODE. You are permitted to generate DDL (CREATE, DROP, ALTER) and DML (INSERT, UPDATE, DELETE) queries as requested by the user."
            task = f"Your task is to convert a user's natural language database administration request into an accurate SQL query for a {dialect.upper()} database."
        else:
            role = "Expert Enterprise SQL Data Analyst"
            security_rule = "Security: Generate STRICTLY read-only SELECT or WITH (CTE) statements. Never generate INSERT, UPDATE, DELETE, DROP, or ALTER commands."
            task = f"Your task is to convert a user's natural language business question into an accurate, efficient, read-only SQL query for a {dialect.upper()} database."

        system_instruction = f"""
You are an {role}.
{task}

Database Schema & Dialect Context:
{schema_info}

CRITICAL INSTRUCTIONS:
1. Return ONLY the raw SQL query. Do NOT add markdown intros, explanations, or commentary outside the query block.
2. Dialect Specific Rules ({dialect.upper()}):
   - For SQLite: Use strftime('%Y', column), strftime('%m', column), datetime functions, or LIKE for dates.
   - For PostgreSQL: Use DATE_TRUNC('month', column), EXTRACT(YEAR FROM column), or standard Postgres date operators.
3. Handle Quarter Queries:
   - Q1: Month 01-03
   - Q2: Month 04-06
   - Q3: Month 07-09
   - Q4: Month 10-12
4. {security_rule}
5. Use clear column aliases so chart labels and metric columns look clean.
"""'''
content = content.replace(old_gen, new_gen)

old_auto = '''    def auto_correct_sql(self, user_question: str, broken_sql: str, error_message: str, schema_info: str, dialect: str = "sqlite") -> str:'''
new_auto = '''    def auto_correct_sql(self, user_question: str, broken_sql: str, error_message: str, schema_info: str, dialect: str = "sqlite", is_admin: bool = False) -> str:'''
content = content.replace(old_auto, new_auto)

with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/ai_engine.py', 'w') as f:
    f.write(content)
print("Updated ai_engine.py for admin mode.")
