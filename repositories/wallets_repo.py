# repositories/wallets_repo.py
from __future__ import annotations
import psycopg2.extras

def get_wallet_by_user_id(conn, user_id: str) -> dict | None:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT current_balance, currency
            FROM wallets
            WHERE user_id = %s
            """,
            (user_id,),
        )
        return cur.fetchone()
