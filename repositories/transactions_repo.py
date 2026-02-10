from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import psycopg


def _fetchone_dict(cur: psycopg.Cursor) -> dict[str, Any] | None:
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d.name for d in cur.description]
    return dict(zip(cols, row))


def _fetchall_dict(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    rows = cur.fetchall()
    if not rows:
        return []
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


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
    with conn.cursor() as cur:
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
        return row[0]


def get_transactions_for_user(
        conn,
        *,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
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
        return _fetchall_dict(cur)


def get_transactions_for_user_in_range(
        conn,
        *,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 20,
        offset: int = 0,
) -> list[dict[str, Any]]:
    """
    מחזיר פעולות של משתמש בטווח תאריכים (כולל).
    """
    with conn.cursor() as cur:
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
            WHERE (from_user_id = %s OR to_user_id = %s)
              AND created_at >= %s
              AND created_at <= %s
            ORDER BY created_at DESC
                LIMIT %s
            OFFSET %s
            """,
            (user_id, user_id, start_date, end_date, limit, offset),
        )
        return _fetchall_dict(cur)
