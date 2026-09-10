"""SQLite connection for the foundation phase. Keep persistence behind this boundary."""
import os
import sqlite3


def connect(path: str | None = None) -> sqlite3.Connection:
    db_path = path or os.getenv("EAGLE_DB_PATH", "eagle.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
