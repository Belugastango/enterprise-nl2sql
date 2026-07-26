import os
import re
import json
from google import genai
from google.genai import types
from typing import Dict, Any, Tuple, Optional

class AIEngine:
    """Interfaces with Gemini API for SQL Generation, Self-Healing, Explanations, Insights, and Visualization Config."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def is_configured(self) -> bool:
        return bool(self.client and self.api_key)

    def _extract_sql_from_text(self, text: str) -> str:
        """Extracts clean SQL code from Markdown blocks or raw text."""
        sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            sql = text.strip()
        
        # Remove any leading markdown text before SELECT/WITH
        sql_clean_match = re.search(r"\b(SELECT|WITH)\b.*", sql, re.DOTALL | re.IGNORECASE)
        if sql_clean_match:
            sql = sql_clean_match.group(0).strip()
            
        return sql.rstrip(';') + ';'

    def generate_sql(self, user_question: str, schema_info: str, dialect: str = "sqlite", is_admin: bool = False) -> str:
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
"""

        prompt = f"User Business Question: \"{user_question}\""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1
                )
            )
            raw_text = response.text or ""
            return self._extract_sql_from_text(raw_text)
        except Exception as e:
            raise RuntimeError(f"Gemini API SQL Generation Error: {str(e)}")

    def auto_correct_sql(self, user_question: str, broken_sql: str, error_message: str, schema_info: str, dialect: str = "sqlite", is_admin: bool = False) -> str:
        """Self-healing loop: fixes broken SQL queries using execution error traceback."""
        if not self.is_configured():
            raise ValueError("Gemini API Key is missing.")

        system_instruction = f"""
You are an expert SQL Debugger. The previous SQL query executed against a {dialect.upper()} database raised an error.
Your task is to fix the SQL query to resolve the error while correctly answering the user's business question.

Database Schema & Dialect Context:
{schema_info}

Execution Failure Context:
- User Question: "{user_question}"
- Broken SQL Query:
```sql
{broken_sql}
```
- Database Error Traceback:
{error_message}

Return ONLY the corrected raw SQL query.
"""

        prompt = "Fix the SQL query and return only the corrected SQL."

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
            raise RuntimeError(f"SQL Auto-Correction Error: {str(e)}")

    def explain_sql(self, sql: str, user_question: str) -> str:
        """Generates a plain-English, step-by-step breakdown of how the SQL query works."""
        if not self.is_configured():
            return "API Key not configured for explanation."

        prompt = f"""
Explain the following SQL query in simple, non-technical plain English for a business manager.

User Question: "{user_question}"
SQL Query:
```sql
{sql}
```

Format your response in bullet points covering:
1. What tables are joined and why.
2. How the data is filtered (e.g. date ranges, conditions).
3. How results are aggregated, ordered, or limited.
Keep it concise, clear, and business-focused.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            )
            return response.text or "No explanation generated."
        except Exception as e:
            return f"Explanation unavailable: {str(e)}"

    def generate_business_insights(self, user_question: str, sql: str, data_preview_md: str) -> str:
        """Synthesizes executive bullet points and insights from query results."""
        if not self.is_configured():
            return "API Key required for business insights."

        prompt = f"""
You are a Lead Data Analyst presenting findings to C-level Executives.
Analyze the following query results and synthesize key business takeaways, highlights, and actionable insights.

User Question: "{user_question}"
SQL Executed:
```sql
{sql}
```
Query Output Data:
{data_preview_md}

Provide:
- **Key Takeaway**: 1 sentence summary of the core finding.
- **Top Highlights**: 2-3 bullet points calling out top metrics, growth drivers, anomalies, or leaders.
- **Executive Recommendation**: 1 strategic next step for management based on this data.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            return response.text or "No insights generated."
        except Exception as e:
            return f"Insights generation error: {str(e)}"

    def recommend_chart_config(self, user_question: str, columns: list, sample_rows: list) -> Dict[str, Any]:
        """Asks Gemini to recommend the optimal Plotly chart configuration as JSON."""
        if not self.is_configured():
            return {}

        system_instruction = """
You are a Visualization Expert. Recommend the optimal Plotly chart type and field mappings for the provided query results.
Return STRICT JSON with keys:
{
  "chart_type": "bar" | "line" | "pie" | "donut" | "area" | "scatter" | "metric",
  "x": "column_name_for_x_axis",
  "y": "column_name_for_y_axis",
  "color": "optional_groupby_column" or null,
  "title": "Suggested Chart Title"
}
"""
        prompt = f"""
Question: "{user_question}"
Columns: {columns}
Sample Rows: {sample_rows[:3]}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            return json.loads(response.text)
        except Exception:
            return {}

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
