with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'r') as f:
    content = f.read()

# 1. Sidebar Toggle
old_sidebar = """    st.markdown("---")
    st.subheader("2. Database Connection")"""
new_sidebar = """    st.markdown("---")
    st.subheader("2. Mode & Privileges")
    app_mode = st.radio(
        "Application Mode",
        ["🔍 Analyst (Read-Only)", "🛠️ Admin (Read/Write)"],
        index=0,
        help="Admin mode allows AI to execute CREATE, DROP, UPDATE queries."
    )
    is_admin_mode = "Admin" in app_mode
    
    st.markdown("---")
    st.subheader("3. Database Connection")"""
content = content.replace(old_sidebar, new_sidebar)

# 2. Header Card
old_header = """# Main Application Layout
st.markdown(\"""
<div class="header-card">
    <div class="header-title">Enterprise Data Intelligence</div>
    <div class="header-subtitle">Empowering business leaders to query databases instantly using plain English — powered by Google Gemini AI & Plotly.</div>
    <div style="margin-top: 14px;">
        <span class="metric-badge">Gemini 2.5 Flash</span>
        <span class="metric-badge">Read-Only Guardrails</span>
        <span class="metric-badge">Dynamic Visualizations</span>
        <span class="metric-badge">Auto-Healing SQL</span>
    </div>
</div>
\""", unsafe_allow_html=True)"""
new_header = """# Main Application Layout
if is_admin_mode:
    guardrails_badge = '<span class="metric-badge" style="background:#FEF2F2; color:#DC2626; border-color:#FCA5A5;">⚠️ Admin Privileges Active</span>'
    st.warning("⚠️ **Admin Mode Active:** The AI can modify database schemas and data. Use with caution.")
else:
    guardrails_badge = '<span class="metric-badge">Read-Only Guardrails</span>'

st.markdown(f\"""
<div class="header-card">
    <div class="header-title">Enterprise Data Intelligence</div>
    <div class="header-subtitle">Empowering business leaders to query databases instantly using plain English — powered by Google Gemini AI & Plotly.</div>
    <div style="margin-top: 14px;">
        <span class="metric-badge">Gemini 2.5 Flash</span>
        {guardrails_badge}
        <span class="metric-badge">Dynamic Visualizations</span>
        <span class="metric-badge">Auto-Healing SQL</span>
    </div>
</div>
\""", unsafe_allow_html=True)"""
content = content.replace(old_header, new_header)

# 3. Method calls
content = content.replace(
    '''                generated_sql = ai_engine.generate_sql(
                    user_question=user_query,
                    schema_info=schema_info,
                    dialect=selected_engine_type
                )''',
    '''                generated_sql = ai_engine.generate_sql(
                    user_question=user_query,
                    schema_info=schema_info,
                    dialect=selected_engine_type,
                    is_admin=is_admin_mode
                )'''
)

content = content.replace(
    'df, elapsed, error = db_mgr.execute_query(generated_sql)',
    'df, elapsed, error = db_mgr.execute_query(generated_sql, is_admin=is_admin_mode)'
)

content = content.replace(
    '''                    fixed_sql = ai_engine.auto_correct_sql(
                        user_question=user_query,
                        broken_sql=generated_sql,
                        error_message=error,
                        schema_info=schema_info,
                        dialect=selected_engine_type
                    )''',
    '''                    fixed_sql = ai_engine.auto_correct_sql(
                        user_question=user_query,
                        broken_sql=generated_sql,
                        error_message=error,
                        schema_info=schema_info,
                        dialect=selected_engine_type,
                        is_admin=is_admin_mode
                    )'''
)

content = content.replace(
    'df, elapsed, error = db_mgr.execute_query(fixed_sql)',
    'df, elapsed, error = db_mgr.execute_query(fixed_sql, is_admin=is_admin_mode)'
)

content = content.replace(
    '''        if st.button("Execute Modified SQL", use_container_width=True):
            df_new, elapsed_new, error_new = db_mgr.execute_query(custom_sql)''',
    '''        if st.button("Execute Modified SQL", use_container_width=True):
            df_new, elapsed_new, error_new = db_mgr.execute_query(custom_sql, is_admin=is_admin_mode)'''
)

with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'w') as f:
    f.write(content)
print("Updated app.py for admin mode.")
