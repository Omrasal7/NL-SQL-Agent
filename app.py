from __future__ import annotations

import sqlite3
from pathlib import Path

import streamlit as st

from config import DEFAULT_DB_PATH, MAX_SCHEMA_PREVIEW_CHARS
from db_utils import ensure_demo_database, fetch_schema_summary, list_tables, run_select_query
from nl_sql_engine import SQLGenerationResult, generate_sql_query, repair_sql_query

st.set_page_config(
    page_title="NL to SQL Agent",
    page_icon="DB",
    layout="wide",
)

st.title("Natural Language to SQL Agent")
st.caption(
    "Ask for data in plain English. The agent reads the table schema, writes a safe SQL query, runs it, and shows the result."
)

default_db = str(Path(DEFAULT_DB_PATH).resolve())

with st.sidebar:
    st.header("Database")
    database_path = st.text_input("SQLite database path", value=default_db)

    if st.button("Create / refresh demo database"):
        ensure_demo_database(database_path)
        st.success("Demo database is ready.")

    st.markdown(
        "Use your own SQLite database path, or keep the demo database to test the flow quickly."
    )

selected_path = Path(database_path).resolve()
is_demo_database = selected_path == Path(default_db).resolve()

try:
    if is_demo_database and not Path(database_path).exists():
        ensure_demo_database(database_path)
    tables = list_tables(database_path)
    schema_summary = fetch_schema_summary(database_path)
    database_error = None
except sqlite3.Error as exc:
    tables = []
    schema_summary = ""
    database_error = str(exc)

col1, col2 = st.columns([3, 2])

with col1:
    user_request = st.text_area(
        "What do you want to know from the database?",
        value="Show the top 5 customers by total order amount.",
        height=140,
        placeholder="Example: List all orders from the last 30 days with customer name and total amount.",
    )

    run_now = st.button("Generate query and fetch data", type="primary", disabled=bool(database_error))

    if database_error:
        st.error(f"Could not open the database: {database_error}")

    if run_now and user_request.strip():
        with st.spinner("Understanding your request and generating SQL..."):
            generated = generate_sql_query(user_request=user_request, schema_summary=schema_summary)

        try:
            columns, rows = run_select_query(database_path, generated.sql)
            final_result: SQLGenerationResult = generated
            st.subheader("Results")
            st.caption(f"{len(rows)} row(s) returned")
            st.dataframe(rows, use_container_width=True)
            if columns:
                st.write(f"Columns: {', '.join(columns)}")
        except ValueError as exc:
            final_result = generated
            st.error(f"Query blocked: {exc}")
        except sqlite3.Error as exc:
            repair_error = str(exc)
            with st.spinner("The first query missed the schema. Repairing it and trying again..."):
                repaired = repair_sql_query(
                    user_request=user_request,
                    schema_summary=schema_summary,
                    failed_sql=generated.sql,
                    execution_error=repair_error,
                )
            try:
                columns, rows = run_select_query(database_path, repaired.sql)
                final_result = repaired
                st.info("The first SQL query failed, so the agent repaired it using the database error message and retried.")
                st.subheader("Results")
                st.caption(f"{len(rows)} row(s) returned")
                st.dataframe(rows, use_container_width=True)
                if columns:
                    st.write(f"Columns: {', '.join(columns)}")
            except (ValueError, sqlite3.Error) as second_exc:
                final_result = repaired
                st.error(f"Database error: {repair_error}")
                st.error(f"Retry also failed: {second_exc}")

        st.subheader("Generated SQL")
        st.code(final_result.sql, language="sql")
        st.write(final_result.explanation)

        if final_result.safety_notes:
            st.subheader("Safety notes")
            for note in final_result.safety_notes:
                st.markdown(f"- {note}")

with col2:
    st.subheader("Available tables")
    if tables:
        for table in tables:
            st.markdown(f"- `{table}`")
    else:
        st.write("No tables found.")

    st.subheader("Schema preview")
    if schema_summary:
        preview = schema_summary[:MAX_SCHEMA_PREVIEW_CHARS]
        st.code(preview, language="text")
        if len(schema_summary) > MAX_SCHEMA_PREVIEW_CHARS:
            st.caption("Schema preview truncated in the sidebar panel.")
    else:
        st.write("Schema will appear here when a database is available.")
