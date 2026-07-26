import os
import re
import json
from typing import Dict, Any, Tuple, Optional

class AIEngine:
    """Interfaces with AI Providers for SQL Generation, Self-Healing, Explanations, Insights, and Visualization Config."""

    def __init__(self, api_provider: str = "gemini", api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_provider = api_provider.lower()
        
        if self.api_provider == "gemini":
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            self.model_name = model_name or "gemini-2.5-flash"
            self.client = None
            if self.api_key:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                
        elif self.api_provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.model_name = model_name or "gpt-4o"
            self.client = None
            if self.api_key:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                
        elif self.api_provider == "deepseek":
            self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
            self.model_name = model_name or "deepseek-coder"
            self.client = None
            if self.api_key:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
                
        elif self.api_provider == "openrouter":
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            self.model_name = model_name or "meta-llama/llama-3.3-70b-instruct"
            self.client = None
            if self.api_key:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")
        else:
            raise ValueError(f"Unsupported API provider: {self.api_provider}")

    def is_configured(self) -> bool:
        return bool(self.client and self.api_key)

    def _call_llm(self, prompt: str, system_instruction: str, temperature: float = 0.1, response_mime_type: Optional[str] = None) -> str:
        """Unified internal method to call the configured LLM provider."""
        if not self.is_configured():
            raise ValueError(f"{self.api_provider.capitalize()} API Key is not configured. Please enter your API key in the sidebar.")
            
        if self.api_provider == "gemini":
            from google.genai import types
            
            # Setup generation config
            config_kwargs = {"temperature": temperature}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            if response_mime_type:
                config_kwargs["response_mime_type"] = response_mime_type
                
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            return response.text or ""
            
        elif self.api_provider in ["openai", "deepseek", "openrouter"]:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature
            }
            if response_mime_type == "application/json" and self.api_provider == "openai":
                kwargs["response_format"] = {"type": "json_object"}
                
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""

    def _extract_sql_from_text(self, text: str) -> str:
        """Extracts clean SQL code from Markdown blocks or raw text."""
        sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            sql = text.strip()
        
        # Remove any leading markdown text before SELECT/WITH/CREATE/ALTER etc
        sql_clean_match = re.search(r"\b(SELECT|WITH|CREATE|DROP|ALTER|INSERT|UPDATE|DELETE)\b.*", sql, re.DOTALL | re.IGNORECASE)
        if sql_clean_match:
            sql = sql_clean_match.group(0).strip()
            
        return sql.rstrip(';') + ';'

    def generate_sql(self, user_question: str, schema_info: str, dialect: str = "sqlite", is_admin: bool = False) -> str:
        """Translates plain English question into dialect-specific SQL query."""
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
            raw_text = self._call_llm(prompt, system_instruction, temperature=0.1)
            return self._extract_sql_from_text(raw_text)
        except Exception as e:
            raise RuntimeError(f"AI SQL Generation Error: {str(e)}")

    def auto_correct_sql(self, user_question: str, broken_sql: str, error_message: str, schema_info: str, dialect: str = "sqlite", is_admin: bool = False) -> str:
        """Self-healing loop: fixes broken SQL queries using execution error traceback."""
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
            raw_text = self._call_llm(prompt, system_instruction, temperature=0.0)
            return self._extract_sql_from_text(raw_text)
        except Exception as e:
            raise RuntimeError(f"SQL Auto-Correction Error: {str(e)}")

    def explain_sql(self, sql: str, user_question: str) -> str:
        """Generates a plain-English, step-by-step breakdown of how the SQL query works."""
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
            return self._call_llm(prompt, system_instruction="", temperature=0.2)
        except Exception as e:
            return f"Explanation unavailable: {str(e)}"

    def generate_business_insights(self, user_question: str, sql: str, data_preview_md: str) -> str:
        """Synthesizes executive bullet points and insights from query results."""
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
            return self._call_llm(prompt, system_instruction="", temperature=0.3)
        except Exception as e:
            return f"Insights generation error: {str(e)}"

    def recommend_chart_config(self, user_question: str, columns: list, sample_rows: list) -> Dict[str, Any]:
        """Asks the AI to recommend the optimal Plotly chart configuration as JSON."""
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
            raw_text = self._call_llm(prompt, system_instruction, temperature=0.1, response_mime_type="application/json")
            
            # Clean up JSON if model returns it inside markdown blocks
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL | re.IGNORECASE)
            if json_match:
                raw_text = json_match.group(1).strip()
            
            return json.loads(raw_text)
        except Exception:
            return {}

    def generate_schema_migration_sql(self, table_name: str, old_schema: str, new_schema: str, dialect: str) -> str:
        """Uses AI to generate ALTER TABLE statements from visual schema edits."""
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
            raw_text = self._call_llm(prompt, system_instruction, temperature=0.0)
            return self._extract_sql_from_text(raw_text)
        except Exception as e:
            raise RuntimeError(f"Schema Migration AI Error: {str(e)}")
