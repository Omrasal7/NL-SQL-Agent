# NL to SQL Agent

This folder contains a self-contained Natural Language to SQL app built with Streamlit, SQLite, and Ollama.

## Files

- `app.py`: Streamlit interface
- `config.py`: app and Ollama settings
- `db_utils.py`: schema inspection, safe SQL validation, and query execution
- `nl_sql_engine.py`: SQL generation and repair logic
- `requirements.txt`: Python dependencies

## Run

1. Open a terminal in `nl-sql`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure Ollama is running with `llama3.2`.
4. Start the app:
   ```bash
   streamlit run app.py
   ```

## Notes

- The default demo database is created at `data/demo_nl_sql.sqlite`.
- You can replace that path in the sidebar with your own SQLite database file.
- Only single-statement read-only `SELECT` queries are allowed.
- If the first generated SQL fails, the app retries once using the SQLite error message and schema.

## Safety

- The app is intentionally read-only and does not allow destructive schema changes.
- Queries such as `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, and `PRAGMA` are blocked.
- Dropping the entire schema is not supported in the current app design.
- If you later want admin capabilities, the safer approach is to add a separate admin mode with explicit confirmation, logging, and backups before destructive actions.
