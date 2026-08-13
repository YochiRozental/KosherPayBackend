from __future__ import annotations

from typing import Any

from psycopg.rows import dict_row


def get_users_overview(conn) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT u.id,
                   u.name,
                   u.role,
                   u.status,
                   up.phone_number,
                   w.current_balance AS balance,
                   w.currency
            FROM users u
                     LEFT JOIN user_phones up
                               ON up.user_id = u.id
                              AND up.is_primary = TRUE
                     LEFT JOIN wallets w
                               ON w.user_id = u.id
            ORDER BY u.id DESC
            """
        )

        return cur.fetchall()


def approve_pending_user(conn, *, user_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET status = 'active',
                updated_at = NOW()
            WHERE id = %s
              AND status = 'pending_approval'
              AND deleted_at IS NULL
            """,
            (user_id,),
        )

        return cur.rowcount > 0


def reject_pending_user(conn, *, user_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET status = 'rejected',
                updated_at = NOW()
            WHERE id = %s
              AND status = 'pending_approval'
              AND deleted_at IS NULL
            """,
            (user_id,),
        )

        return cur.rowcount > 0


def block_active_user(conn, *, user_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET status = 'blocked',
                updated_at = NOW()
            WHERE id = %s
              AND status = 'active'
              AND deleted_at IS NULL
            """,
            (user_id,),
        )

        return cur.rowcount > 0


def unblock_user(conn, *, user_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET status = 'active',
                updated_at = NOW()
            WHERE id = %s
              AND status = 'blocked'
              AND deleted_at IS NULL
            """,
            (user_id,),
        )

        return cur.rowcount > 0
