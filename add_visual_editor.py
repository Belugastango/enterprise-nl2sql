with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'r') as f:
    content = f.read()

editor_ui = """
# ---------------------------------------------------------
# Visual Schema Editor (Admin Mode Only)
# ---------------------------------------------------------
if is_admin_mode and conn_ok:
    st.markdown("---")
    st.subheader("🛠️ Visual Schema Editor")
    st.caption("Add, rename, or drop columns. AI will automatically write and execute the migration SQL.")
    
    tables = list(db_mgr.get_schema_details().keys())
    if tables:
        selected_table = st.selectbox("Select Table to Edit:", ["-- Select Table --"] + tables)
        if selected_table != "-- Select Table --":
            old_df = db_mgr.get_table_schema_df(selected_table)
            st.write("Edit columns (Add rows to create columns, delete rows to drop columns):")
            
            new_df = st.data_editor(
                old_df,
                num_rows="dynamic",
                key=f"editor_{selected_table}",
                use_container_width=True
            )
            
            if st.button("Apply Schema Changes", type="primary"):
                with st.spinner("AI is analyzing changes and generating migration SQL..."):
                    try:
                        migration_sql = ai_engine.generate_schema_migration_sql(
                            table_name=selected_table,
                            old_schema=old_df.to_markdown(index=False),
                            new_schema=new_df.to_markdown(index=False),
                            dialect=selected_engine_type
                        )
                        st.info("Generated Migration SQL:")
                        st.code(migration_sql, language="sql")
                        
                        df_mig, elapsed_mig, err_mig = db_mgr.execute_query(migration_sql, is_admin=True)
                        if err_mig:
                            st.error(f"Migration Failed: {err_mig}")
                        else:
                            st.success(f"Migration applied successfully in {elapsed_mig:.2f}s!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"AI Migration Error: {str(e)}")
"""

# Append it at the end of app.py
with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'a') as f:
    f.write(editor_ui)

print("Added Visual Schema Editor to app.py")
