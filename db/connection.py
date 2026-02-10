import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT", "5432")),
            connect_timeout=5,
            sslmode="require",
            row_factory=dict_row,
        )
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
