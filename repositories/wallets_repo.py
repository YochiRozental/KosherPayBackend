from __future__ import annotations

from typing import Any


def get_wallet_by_user_id(conn, user_id: str) -> dict[str, Any] | None:
    user_id = (user_id or "").strip()
    if not user_id:
        return None

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT current_balance,
                   currency
            FROM wallets
            WHERE user_id = %s LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        return {
            "current_balance": row[0],
            "currency": row[1],
        }
