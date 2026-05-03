from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import requests

from config import OLLAMA_MODEL, OLLAMA_URL, REQUEST_TIMEOUT


@dataclass
class SQLGenerationResult:
    sql: str
    explanation: str
    safety_notes: list[str] = field(default_factory=list)
    used_fallback: bool = False


def generate_sql_query(user_request: str, schema_summary: str) -> SQLGenerationResult:
    prompt = _build_prompt(user_request=user_request, schema_summary=schema_summary)

    try:
        llm_output = _generate_response(prompt)
        payload = _parse_json(llm_output)
        return SQLGenerationResult(
            sql=payload["sql"],
            explanation=payload["explanation"],
            safety_notes=payload.get("safety_notes", []),
            used_fallback=False,
        )
    except Exception:
        return _fallback_query(user_request=user_request, schema_summary=schema_summary)


def repair_sql_query(
    user_request: str,
    schema_summary: str,
    failed_sql: str,
    execution_error: str,
) -> SQLGenerationResult:
    prompt = _build_repair_prompt(
        user_request=user_request,
        schema_summary=schema_summary,
        failed_sql=failed_sql,
        execution_error=execution_error,
    )

    try:
        llm_output = _generate_response(prompt)
        payload = _parse_json(llm_output)
        notes = payload.get("safety_notes", [])
        notes.append(f"Repaired after SQLite error: {execution_error}")
        return SQLGenerationResult(
            sql=payload["sql"],
            explanation=payload["explanation"],
            safety_notes=notes,
            used_fallback=False,
        )
    except Exception:
        fallback = _fallback_query(user_request=user_request, schema_summary=schema_summary)
        fallback.safety_notes.append(f"Repair mode fell back after SQLite error: {execution_error}")
        return fallback


def _build_prompt(user_request: str, schema_summary: str) -> str:
    return f"""
You are a careful SQLite analyst.

Your job:
1. Read the user's analytics request.
2. Read the available database schema.
3. Write one SQL query that answers the request.
4. The query must be valid SQLite.
5. The query must be read-only.
6. Return only JSON.

Rules:
- Only use SELECT or WITH ... SELECT.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, or multiple statements.
- Prefer explicit column names.
- Add LIMIT when the user asks for lists but gives no limit.
- Use only column names that appear exactly in the schema below.
- If a requested field does not exist, choose the closest valid column from the schema instead of inventing one.

Return JSON with this exact shape:
{{
  "sql": "SELECT ...",
  "explanation": "short explanation of what the query does",
  "safety_notes": ["note 1", "note 2"]
}}

Schema:
{schema_summary}

User request:
{user_request}
""".strip()


def _build_repair_prompt(
    user_request: str,
    schema_summary: str,
    failed_sql: str,
    execution_error: str,
) -> str:
    return f"""
You are repairing a failed SQLite query.

The user request was:
{user_request}

The available schema is:
{schema_summary}

The previous SQL failed:
{failed_sql}

SQLite returned this error:
{execution_error}

Write a corrected read-only SQLite query that uses only real tables and columns from the schema.

Rules:
- Only use SELECT or WITH ... SELECT.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, or multiple statements.
- Use only column names that appear exactly in the schema.
- Return only JSON in this format:
{{
  "sql": "SELECT ...",
  "explanation": "short explanation of the fix",
  "safety_notes": ["note 1", "note 2"]
}}
""".strip()


def _generate_response(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


def _parse_json(text: str) -> dict[str, object]:
    raw = text.strip()
    if not raw:
        raise ValueError("Empty response from model.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _fallback_query(user_request: str, schema_summary: str) -> SQLGenerationResult:
    table_names = re.findall(r"Table: ([A-Za-z_][A-Za-z0-9_]*)", schema_summary)
    chosen_table = _pick_table(user_request, table_names) or (table_names[0] if table_names else "orders")
    request_lower = user_request.lower()

    if "count" in request_lower or "how many" in request_lower:
        sql = f"SELECT COUNT(*) AS row_count FROM {chosen_table}"
        explanation = f"Counts rows from the `{chosen_table}` table."
    elif "top" in request_lower and "customer" in request_lower and {"orders", "customers"}.issubset(set(table_names)):
        sql = """
SELECT
    c.customer_name,
    SUM(o.total_amount) AS total_spend
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
GROUP BY c.customer_name
ORDER BY total_spend DESC
LIMIT 5
""".strip()
        explanation = "Ranks customers by summed order value and returns the top 5."
    else:
        sql = f"SELECT * FROM {chosen_table} LIMIT 25"
        explanation = f"Shows a sample of rows from the `{chosen_table}` table."

    return SQLGenerationResult(
        sql=sql,
        explanation=explanation,
        safety_notes=[
            "Fallback mode was used because the language model was unavailable or returned invalid JSON.",
            "The fallback generator supports only simple patterns; connect Ollama for better SQL generation.",
        ],
        used_fallback=True,
    )


def _pick_table(user_request: str, table_names: list[str]) -> str | None:
    lowered_request = user_request.lower()
    for table_name in table_names:
        singular_name = table_name[:-1] if table_name.endswith("s") else table_name
        if table_name.lower() in lowered_request or singular_name.lower() in lowered_request:
            return table_name
    return None
