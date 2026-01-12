# repositories/payment_requests_repo.py
from __future__ import annotations
import psycopg2.extras

def create_payment_request(
    conn,
    *,
    requester_id: str,
    recipient_id: str,
    amount: float,
) -> dict:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO payment_requests
                (requester_id, recipient_id, amount, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id, requester_id, recipient_id, amount, status, created_at
            """,
            (requester_id, recipient_id, amount),
        )
        return cur.fetchone()


def get_pending_requests_for_user(conn, *, user_id: str) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, requester_id, recipient_id, amount, status, created_at
            FROM payment_requests
            WHERE recipient_id = %s
              AND status = 'pending'
            ORDER BY created_at ASC
            """,
            (user_id,),
        )
        return cur.fetchall()


def approve_pending_request_atomic(conn, *, request_id: int, recipient_id: str) -> dict | None:
    """
    Approves only if currently pending and belongs to recipient_id.
    Atomic -> prevents double approval.
    Returns requester_id/amount if approved, else None.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            UPDATE payment_requests
            SET status = 'approved'
            WHERE id = %s
              AND recipient_id = %s
              AND status = 'pending'
            RETURNING requester_id, recipient_id, amount
            """,
            (request_id, recipient_id),
        )
        return cur.fetchone()


def reject_pending_request_atomic(conn, *, request_id: int, recipient_id: str) -> bool:
    """
    Rejects only if pending and belongs to recipient_id.
    Returns True if changed, else False.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE payment_requests
            SET status = 'rejected'
            WHERE id = %s
              AND recipient_id = %s
              AND status = 'pending'
            """,
            (request_id, recipient_id),
        )
        return cur.rowcount == 1
