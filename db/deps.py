# db/deps.py
from __future__ import annotations
from collections.abc import Generator
from db.connection import get_db_connection

def get_db() -> Generator:
    """
    FastAPI dependency: yields a single DB connection per request.
    Transaction is committed/rolled back in get_db_connection().
    """
    with get_db_connection() as conn:
        yield conn
