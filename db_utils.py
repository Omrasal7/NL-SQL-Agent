from __future__ import annotations

import sqlite3
from pathlib import Path

from config import MAX_RESULT_ROWS


FORBIDDEN_SQL_TOKENS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "attach",
    "detach",
    "pragma",
}


def ensure_demo_database(database_path: str) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA journal_mode=MEMORY")
        connection.execute("PRAGMA synchronous=OFF")
        cursor = connection.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                city TEXT NOT NULL,
                segment TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_price REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );
            """
        )

        has_rows = cursor.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if has_rows:
            return

        cursor.executemany(
            "INSERT INTO customers (customer_id, customer_name, city, segment) VALUES (?, ?, ?, ?)",
            [
                (1, "Acme Retail", "Mumbai", "Retail"),
                (2, "Northwind Foods", "Delhi", "Wholesale"),
                (3, "Blue Ocean Tech", "Bengaluru", "Enterprise"),
                (4, "Sunrise Health", "Hyderabad", "Healthcare"),
                (5, "Urban Cart", "Pune", "Retail"),
            ],
        )
        cursor.executemany(
            "INSERT INTO products (product_id, product_name, category, unit_price) VALUES (?, ?, ?, ?)",
            [
                (1, "Analytics Suite", "Software", 1200.0),
                (2, "Support Plan", "Service", 300.0),
                (3, "IoT Sensor", "Hardware", 150.0),
                (4, "Security License", "Software", 800.0),
            ],
        )
        cursor.executemany(
            """
            INSERT INTO orders (order_id, customer_id, product_id, order_date, quantity, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (1001, 1, 1, "2026-04-10", 2, 2400.0),
                (1002, 2, 2, "2026-04-11", 5, 1500.0),
                (1003, 3, 4, "2026-04-12", 3, 2400.0),
                (1004, 1, 3, "2026-04-15", 10, 1500.0),
                (1005, 4, 1, "2026-04-18", 1, 1200.0),
                (1006, 5, 2, "2026-04-20", 4, 1200.0),
                (1007, 3, 1, "2026-04-23", 2, 2400.0),
                (1008, 2, 3, "2026-04-24", 12, 1800.0),
                (1009, 5, 4, "2026-04-25", 2, 1600.0),
                (1010, 4, 2, "2026-04-27", 6, 1800.0),
            ],
        )
        connection.commit()


def list_tables(database_path: str) -> list[str]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
    return [row[0] for row in rows]


def fetch_schema_summary(database_path: str) -> str:
    summaries: list[str] = []
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        for table_name in list_tables(database_path):
            columns = connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            column_lines = [
                f"- {column['name']} {column['type']} {'PRIMARY KEY' if column['pk'] else ''}".strip()
                for column in columns
            ]
            sample_rows = connection.execute(f"SELECT * FROM '{table_name}' LIMIT 3").fetchall()
            sample_lines = [str({key: row[key] for key in row.keys()}) for row in sample_rows]
            summaries.append(
                "\n".join(
                    [
                        f"Table: {table_name}",
                        "Columns:",
                        *column_lines,
                        "Sample rows:",
                        *(sample_lines or ["- No rows"]),
                    ]
                )
            )
    return "\n\n".join(summaries)


def validate_select_query(sql: str) -> str:
    normalized = " ".join(sql.strip().split())
    if not normalized:
        raise ValueError("Empty SQL query.")

    lowered = normalized.lower()
    if ";" in normalized.rstrip(";"):
        raise ValueError("Only a single SQL statement is allowed.")
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Only SELECT queries are allowed.")
    if any(token in lowered for token in FORBIDDEN_SQL_TOKENS):
        raise ValueError("The generated SQL contains a blocked operation.")

    return normalized.rstrip(";")


def run_select_query(database_path: str, sql: str) -> tuple[list[str], list[dict[str, object]]]:
    safe_sql = validate_select_query(sql)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(safe_sql)
        rows = cursor.fetchmany(MAX_RESULT_ROWS)
        columns = [item[0] for item in cursor.description] if cursor.description else []
        return columns, [{key: row[key] for key in row.keys()} for row in rows]
