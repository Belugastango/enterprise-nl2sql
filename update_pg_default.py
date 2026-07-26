with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'r') as f:
    content = f.read()

old_radio = """    db_type = st.radio(
        "Database Source",
        ["SQLite Sample DB (Instant Demo)", "PostgreSQL (Live Instance)"],
        index=0
    )"""

new_radio = """    db_type = st.radio(
        "Database Source",
        ["SQLite Sample DB (Instant Demo)", "PostgreSQL (Live Instance)"],
        index=1
    )"""
content = content.replace(old_radio, new_radio)

old_pass = 'pg_pass = st.text_input("Password", type="password", value="")'
new_pass = 'pg_pass = st.text_input("Password", type="password", value="mayank")'
content = content.replace(old_pass, new_pass)

with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'w') as f:
    f.write(content)
print("Updated app.py with Postgres default.")
