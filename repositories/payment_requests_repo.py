from __future__ import annotations

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


def create_payment_request(
        conn,
        *,
        requester_id: str,
        recipient_id: str,
        amount: float,
) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO payment_requests
                (requester_id, recipient_id, amount, status)
            VALUES (%s, %s, %s, 'pending') RETURNING
                id::text AS id,
                requester_id,
                recipient_id,
                amount,
                status,
                created_at
            """,
            (requester_id, recipient_id, amount),
        )
        row = _fetchone_dict(cur)
        return row or {}


def get_sent_requests_for_user(conn, *, user_id: str) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT pr.id::text AS id, pr.requester_id,
                   pr.recipient_id,
                   pr.amount,
                   pr.status,
                   pr.created_at,

                   u_rec.name          AS recipient_name,
                   up_rec.phone_number AS recipient_phone
            FROM payment_requests pr
                     LEFT JOIN users u_rec
                               ON u_rec.id = pr.recipient_id
                     LEFT JOIN user_phones up_rec
                               ON up_rec.user_id = pr.recipient_id
                                   AND up_rec.is_primary = TRUE
            WHERE pr.requester_id = %s
            ORDER BY pr.created_at DESC
            """,
            (user_id,),
        )
        return _fetchall_dict(cur)


def get_requests_for_user(conn, *, user_id: str) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT pr.id::text AS id, pr.requester_id,
                   pr.recipient_id,
                   pr.amount,
                   pr.status,
                   pr.created_at,
                   pr.resolved_at,

                   u_req.name          AS requester_name,
                   up_req.phone_number AS requester_phone
            FROM payment_requests pr
                     LEFT JOIN users u_req
                               ON u_req.id = pr.requester_id
                     LEFT JOIN user_phones up_req
                               ON up_req.user_id = pr.requester_id
                                   AND up_req.is_primary = TRUE
            WHERE pr.recipient_id = %s
            ORDER BY pr.created_at ASC
            """,
            (user_id,),
        )
        return _fetchall_dict(cur)


def approve_pending_request_atomic(
        conn, *, request_id: str, recipient_id: str
) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE payment_requests
            SET status      = 'approved',
                resolved_at = NOW()
            WHERE id::text = %s
              AND recipient_id = %s
              AND status = 'pending'
                RETURNING
                id::text AS id
                , requester_id
                , recipient_id
                , amount
            """,
            (request_id, recipient_id),
        )
        return _fetchone_dict(cur)


def reject_pending_request_atomic(
        conn, *, request_id: str, recipient_id: str
) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE payment_requests
            SET status      = 'rejected',
                resolved_at = NOW()
            WHERE id::text = %s
              AND recipient_id = %s
              AND status = 'pending'
                RETURNING
                id::text AS id
                , requester_id
                , recipient_id
                , amount
            """,
            (request_id, recipient_id),
        )
        return _fetchone_dict(cur)
