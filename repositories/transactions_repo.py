from __future__ import annotations

import uuid

import psycopg2.extras


def get_transactions_for_user(
        conn,
        *,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id,
                   type,
                   amount,
                   currency,
                   status,
                   description,
                   from_user_id,
                   to_user_id,
                   created_at
            FROM transactions
            WHERE from_user_id = %s
               OR to_user_id = %s
            ORDER BY created_at DESC
                LIMIT %s
            OFFSET %s
            """,
            (user_id, user_id, limit, offset),
        )
        return cur.fetchall()


def create_transaction(
        conn,
        *,
        tx_type: str,
        amount: float,
        currency: str = "ILS",
        status: str = "completed",
        from_user_id: str | None,
        to_user_id: str | None,
        description: str,
        related_request_id: str | None = None,
        related_transaction_id: str | None = None,
) -> uuid.UUID:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO transactions (type,
                                      amount,
                                      currency,
                                      status,
                                      description,
                                      from_user_id,
                                      to_user_id,
                                      related_request_id,
                                      related_transaction_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (
                tx_type,
                amount,
                currency,
                status,
                description,
                from_user_id,
                to_user_id,
                related_request_id,
                related_transaction_id,
            ),
        )
        row = cur.fetchone()
        return row["id"]
