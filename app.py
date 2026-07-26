import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from db_manager import DatabaseManager
from ai_engine import AIEngine
from chart_builder import auto_detect_chart_config, create_plotly_figure
from sample_db_seed import create_and_seed_db, DB_PATH

# Load environment variables
load_dotenv()

# Streamlit Page Config
st.set_page_config(
    page_title="Enterprise Data Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Corporate Dashboard Aesthetic
CUSTOM_CSS = """
<style>
    /* Light Corporate theme overrides */
    .main {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Header Card */
    .header-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .header-title {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 8px;
    }
    .header-subtitle {
        color: #475569;
        font-size: 1.05rem;
    }

    /* Metric Badges */
    .metric-badge {
        display: inline-block;
        background: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
        margin-top: 8px;
    }

    /* Sample Questions Container */
    .sample-chip {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        color: #334155;
        padding: 10px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .sample-chip:hover {
        border-color: #94A3B8;
        background: #F8FAFC;
    }
    
    /* Executive Insight Card */
    .insight-card {
        background: #F0FDF4;
        border-left: 4px solid #16A34A;
        border-radius: 4px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #166534;
    }

    /* Security Warning Card */
    .security-card {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        border-radius: 4px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #991B1B;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Ensure sample database exists
if not os.path.exists(DB_PATH):
    create_and_seed_db(DB_PATH)

# Initialize Session State
if "query_input" not in st.session_state:
    st.session_state["query_input"] = ""
if "active_sql" not in st.session_state:
    st.session_state["active_sql"] = ""
if "df_result" not in st.session_state:
    st.session_state["df_result"] = None
if "exec_time" not in st.session_state:
    st.session_state["exec_time"] = 0.0
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = None
if "explanation" not in st.session_state:
    st.session_state["explanation"] = None
if "insights" not in st.session_state:
    st.session_state["insights"] = None
if "chart_config" not in st.session_state:
    st.session_state["chart_config"] = None

# Sidebar - Settings & DB Connection
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/100/database-setting.png", width=64)
    st.title("Settings & DB Config")

    st.subheader("1. AI Engine (Gemini)")
    env_api_key = os.getenv("GEMINI_API_KEY", "")
    if not env_api_key:
        try:
            env_api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
    user_api_key = st.text_input(
        "Gemini API Key",
        value=env_api_key,
        type="password",
        help="Get your key from Google AI Studio (aistudio.google.com)"
    )

    model_choice = st.selectbox(
        "Gemini Model",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        index=0
    )

    st.markdown("---")
    st.subheader("2. Mode & Privileges")
    app_mode = st.radio(
        "Application Mode",
        ["🔍 Analyst (Read-Only)", "🛠️ Admin (Read/Write)"],
        index=0,
        help="Admin mode allows AI to execute CREATE, DROP, UPDATE queries."
    )
    is_admin_mode = "Admin" in app_mode
    
    st.markdown("---")
    st.subheader("3. Database Connection")

    db_type = st.radio(
        "Database Source",
        ["SQLite Sample DB (Instant Demo)", "PostgreSQL (Live Instance)"],
        index=0,
        help="Use SQLite for instant demo. PostgreSQL requires an internet-facing database when deployed on Streamlit Cloud."
    )

    pg_config = {}
    if db_type == "PostgreSQL (Live Instance)":
        pg_host = st.text_input("Host", value="localhost")
        pg_port = st.number_input("Port", value=5432)
        pg_db = st.text_input("Database Name", value="analytics_db")
        pg_user = st.text_input("Username", value="postgres")
        pg_pass = st.text_input("Password", type="password", value="mayank")
        pg_config = {
            "host": pg_host,
            "port": pg_port,
            "dbname": pg_db,
            "user": pg_user,
            "password": pg_pass
        }

    # Instantiation of DB Manager
    selected_engine_type = "sqlite" if "SQLite" in db_type else "postgresql"
    db_mgr = DatabaseManager(db_type=selected_engine_type, db_path=DB_PATH, pg_config=pg_config)
    
    conn_ok, conn_msg = db_mgr.test_connection()
    if conn_ok:
        st.success(f"DB Connected ({selected_engine_type.upper()})")
    else:
        st.error(f"Connection Failed: {conn_msg}")

    if selected_engine_type == "sqlite":
        if st.button("Reset / Re-seed Sample Database"):
            create_and_seed_db(DB_PATH)
            st.toast("Sample database re-seeded successfully!", icon="✅")

    st.markdown("---")
    st.caption("Antigravity AI Data Analyst v2.5")

# Initialize AI Engine
ai_engine = AIEngine(api_key=user_api_key, model_name=model_choice)

# Main Application Layout
if is_admin_mode:
    guardrails_badge = '<span class="metric-badge" style="background:#FEF2F2; color:#DC2626; border-color:#FCA5A5;">⚠️ Admin Privileges Active</span>'
    st.warning("⚠️ **Admin Mode Active:** The AI can modify database schemas and data. Use with caution.")
else:
    guardrails_badge = '<span class="metric-badge">Read-Only Guardrails</span>'

st.markdown(f"""
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
""", unsafe_allow_html=True)

# Sample Questions Prompt Bar
st.markdown("##### Try Asking One of These Business Questions:")

sample_cols = st.columns(3)
sample_questions = [
    "What were our top 3 best-selling products last quarter?",
    "Monthly revenue trend by product category in 2025",
    "Which sales reps exceeded their quarterly targets in Q4 2025?",
    "Top 5 customers by total order spend",
    "Average discount percentage by customer segment",
    "Low stock products with inventory less than 100 units"
]

for idx, q in enumerate(sample_questions):
    col = sample_cols[idx % 3]
    if col.button(f"{q}", key=f"sq_{idx}", use_container_width=True):
        st.session_state["query_input"] = q

# Query Input Form
with st.form("nl_query_form"):
    user_query = st.text_area(
        "Ask a Business Question in Plain English:",
        value=st.session_state["query_input"],
        placeholder="e.g. Compare total revenue by region for 2025 and 2026...",
        height=90
    )
    submit_button = st.form_submit_button("Run Analysis", use_container_width=True)

if submit_button and user_query.strip():
    st.session_state["query_input"] = user_query.strip()
    
    if not conn_ok:
        st.error(f"⚠️ Cannot run analysis. Database Connection Error: {conn_msg}")
    elif not ai_engine.is_configured():
        st.error("⚠️ Please provide a valid Gemini API Key in the sidebar settings.")
    else:
        with st.spinner("🔍 Inspecting Database Schema & Generating SQL via Gemini AI..."):
            try:
                schema_info = db_mgr.get_schema_summary()
                generated_sql = ai_engine.generate_sql(
                    user_question=user_query,
                    schema_info=schema_info,
                    dialect=selected_engine_type,
                    is_admin=is_admin_mode
                )
                
                st.session_state["active_sql"] = generated_sql
                
                # Execute Query with Auto-Healing retry loop
                df, elapsed, error = db_mgr.execute_query(generated_sql, is_admin=is_admin_mode)
                
                # Auto-healing if syntax or schema mismatch error occurs
                if error and "Security Error" not in error:
                    st.warning(f"⚠️ Initial query encountered a database error. Gemini is auto-correcting...")
                    fixed_sql = ai_engine.auto_correct_sql(
                        user_question=user_query,
                        broken_sql=generated_sql,
                        error_message=error,
                        schema_info=schema_info,
                        dialect=selected_engine_type,
                        is_admin=is_admin_mode
                    )
                    st.session_state["active_sql"] = fixed_sql
                    df, elapsed, error = db_mgr.execute_query(fixed_sql, is_admin=is_admin_mode)

                st.session_state["df_result"] = df
                st.session_state["exec_time"] = elapsed
                st.session_state["error_msg"] = error

                if df is not None and not df.empty:
                    # Generate Explanation & Insights asynchronously/parallel
                    st.session_state["explanation"] = ai_engine.explain_sql(st.session_state["active_sql"], user_query)
                    st.session_state["insights"] = ai_engine.generate_business_insights(
                        user_query,
                        st.session_state["active_sql"],
                        df.head(10).to_markdown()
                    )
                    
                    # Recommend Chart Config
                    recommended_config = ai_engine.recommend_chart_config(
                        user_query,
                        list(df.columns),
                        df.head(3).to_dict(orient="records")
                    )
                    if not recommended_config:
                        recommended_config = auto_detect_chart_config(df)
                    st.session_state["chart_config"] = recommended_config
                    
            except Exception as e:
                st.error(f"❌ Analysis Generation Error: {str(e)}")

# Display Results & Tabs if query active
if st.session_state["active_sql"]:
    st.markdown("---")
    
    # Check for execution security error
    if st.session_state["error_msg"]:
        st.markdown(f"""
        <div class="security-card">
            <h4>❌ Query Execution Error</h4>
            <p>{st.session_state['error_msg']}</p>
        </div>
        """, unsafe_allow_html=True)

    tab_results, tab_insights, tab_sql, tab_schema = st.tabs([
        "Results & Visualizations",
        "Executive Insights",
        "SQL Explanation & Query Editor",
        "Database Schema Explorer"
    ])

    # TAB 1: Results & Charts
    with tab_results:
        df = st.session_state["df_result"]
        if df is not None and not df.empty:
            st.markdown(f"**Query Performance**: Executed in `{st.session_state['exec_time']:.3f}s` | Returns `{len(df)}` rows.")
            
            # Chart controls & figure rendering
            chart_config = st.session_state["chart_config"] or auto_detect_chart_config(df)
            
            col_chart_opts, col_chart_view = st.columns([1, 3])
            
            with col_chart_opts:
                st.markdown("##### Visualization Controls")
                selected_chart_type = st.selectbox(
                    "Chart Type",
                    ["bar", "line", "donut", "pie", "area", "scatter", "table"],
                    index=["bar", "line", "donut", "pie", "area", "scatter", "table"].index(
                        chart_config.get("chart_type", "bar") if chart_config.get("chart_type") in ["bar", "line", "donut", "pie", "area", "scatter", "table"] else "bar"
                    )
                )
                
                num_cols = list(df.select_dtypes(include=['number']).columns)
                all_cols = list(df.columns)
                
                x_axis = st.selectbox("X-Axis / Dimension", all_cols, index=all_cols.index(chart_config.get("x")) if chart_config.get("x") in all_cols else 0)
                y_axis = st.selectbox("Y-Axis / Metric", num_cols if num_cols else all_cols, index=num_cols.index(chart_config.get("y")) if chart_config.get("y") in num_cols else 0)
                
                chart_config_updated = {
                    "chart_type": selected_chart_type,
                    "x": x_axis,
                    "y": y_axis,
                    "names": x_axis,
                    "values": y_axis,
                    "color": chart_config.get("color")
                }

            with col_chart_view:
                if selected_chart_type != "table":
                    fig = create_plotly_figure(df, chart_config_updated, title=st.session_state["query_input"])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Chart preview unavailable for selected columns.")

            st.markdown("##### Data Table View")
            st.dataframe(df, use_container_width=True)
            
            # CSV Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv"
            )

        elif df is not None and df.empty:
            st.info("ℹ️ Query executed successfully, but returned 0 rows.")

    # TAB 2: Executive Insights
    with tab_insights:
        if st.session_state["insights"]:
            st.markdown(f"""
            <div class="insight-card">
                <h3>Executive Business Takeaways</h3>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(st.session_state["insights"])
        else:
            st.info("Execute a query to see AI-generated executive insights.")

    # TAB 3: SQL Explanation & Custom SQL Editor
    with tab_sql:
        st.markdown("##### Review & Edit Generated SQL")
        custom_sql = st.text_area(
            "SQL Query:",
            value=st.session_state["active_sql"],
            height=160
        )
        
        if st.button("Execute Modified SQL", use_container_width=True):
            df_new, elapsed_new, error_new = db_mgr.execute_query(custom_sql, is_admin=is_admin_mode)
            st.session_state["active_sql"] = custom_sql
            st.session_state["df_result"] = df_new
            st.session_state["exec_time"] = elapsed_new
            st.session_state["error_msg"] = error_new
            st.rerun()

        st.markdown("---")
        st.markdown("##### Plain English SQL Breakdown")
        if st.session_state["explanation"]:
            st.markdown(st.session_state["explanation"])

    # TAB 4: Database Schema Explorer
    with tab_schema:
        st.markdown("##### Database Schema & Sample Rows")
        schema_details = db_mgr.get_schema_details()
        
        for table_name, df_sample in schema_details.items():
            with st.expander(f"Table: `{table_name}` ({len(df_sample.columns)} columns)"):
                st.dataframe(df_sample, use_container_width=True)

else:
    # Default State when no query is run yet
    st.markdown("---")
    st.info("Select a sample question above or type your own question to start analyzing data.")
    
    with st.expander("View Database Schema Overview"):
        if conn_ok:
            st.markdown(db_mgr.get_schema_summary())
        else:
            st.error(f"❌ Database connection offline: {conn_msg}")

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
