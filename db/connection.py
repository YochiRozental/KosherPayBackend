# -*- coding: utf-8 -*-
# import pymysql
# from config import DB_CONFIG
#
# @contextmanager
# def get_db_connection():
#     connection = None
#     try:
#         connection = pymysql.connect(**DB_CONFIG)
#         yield connection
#     except Exception as e:
#         print(f"שגיאה בחיבור למסד הנתונים: {e}")
#         raise ConnectionError("Connection to database failed") from e
#     finally:
#         if connection:
#             connection.close()

from contextlib import contextmanager
import psycopg2
import psycopg2.extras
import os

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", 5432),
            sslmode="require",
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
