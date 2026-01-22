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
            VALUES (%s, %s, %s,
                    'pending') RETURNING id::text AS id, requester_id, recipient_id, amount, status, created_at
            """,
            (requester_id, recipient_id, amount),
        )
        return cur.fetchone()


# def get_pending_requests_for_user(conn, *, user_id: str) -> list[dict]:
#     with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
#         cur.execute(
#             """
#             SELECT pr.id::text AS id, pr.requester_id,
#                    pr.recipient_id,
#                    pr.amount,
#                    pr.status,
#                    pr.created_at,
#
#                    u_req.name          AS requester_name,
#                    up_req.phone_number AS requester_phone
#             FROM payment_requests pr
#                      LEFT JOIN users u_req
#                                ON u_req.id = pr.requester_id
#                      LEFT JOIN user_phones up_req
#                                ON up_req.user_id = pr.requester_id
#                                    AND up_req.is_primary = TRUE
#             WHERE pr.recipient_id = %s
#               AND pr.status = 'pending'
#             ORDER BY pr.created_at ASC
#             """,
#             (user_id,),
#         )
#         return cur.fetchall()


def get_sent_requests_for_user(conn, *, user_id: str) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
        return cur.fetchall()


def get_requests_for_user(conn, *, user_id: str) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
        return cur.fetchall()


def approve_pending_request_atomic(conn, *, request_id: str, recipient_id: str) -> dict | None:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
        return cur.fetchone()


def reject_pending_request_atomic(conn, *, request_id: str, recipient_id: str) -> dict | None:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
        return cur.fetchone()
