with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'r') as f:
    content = f.read()

csv_ui = """
# ---------------------------------------------------------
# CSV Import (Admin Mode Only)
# ---------------------------------------------------------
if is_admin_mode and conn_ok:
    st.markdown("---")
    st.subheader("📁 Import CSV Data")
    st.caption("Upload a CSV file to automatically create and populate a new table in the database.")
    
    with st.form("csv_upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
        col1, col2 = st.columns(2)
        with col1:
            csv_table_name = st.text_input("Target Table Name", placeholder="e.g. historical_sales")
        with col2:
            if_exists_behavior = st.selectbox("If table exists:", ["fail", "replace", "append"], index=0)
            
        csv_submit = st.form_submit_button("Import to Database", type="primary")
        
        if csv_submit:
            if not uploaded_file:
                st.error("Please select a file to upload.")
            elif not csv_table_name.strip():
                st.error("Please provide a valid table name.")
            else:
                with st.spinner(f"Importing {uploaded_file.name} to {csv_table_name}..."):
                    success, msg = db_mgr.import_csv_to_table(uploaded_file, csv_table_name, if_exists_behavior)
                    if success:
                        st.success(msg)
                        # We use a toast and then sleep briefly, or just don't rerun immediately so user sees message.
                        # Wait, st.rerun clears the success message immediately unless it's in a toast.
                        # We'll just let it render without rerun, or we can use st.toast
                        pass
                    else:
                        st.error(msg)
"""

with open('/Users/mayankkumar/.gemini/antigravity/scratch/nl2sql_data_analyst/app.py', 'a') as f:
    f.write(csv_ui)

print("Added CSV UI to app.py")
