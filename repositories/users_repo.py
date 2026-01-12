# repositories/users_repo.py
from __future__ import annotations
import psycopg2.extras

def get_user_id_by_phone(conn, phone_number: str) -> str | None:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT user_id
            FROM user_phones
            WHERE phone_number = %s
            LIMIT 1
            """,
            (phone_number,),
        )
        row = cur.fetchone()
        return str(row["user_id"]) if row else None


def get_user_for_auth(conn, phone_number: str) -> dict | None:
    """
    Returns data needed for login/auth:
    user_id, role, status, phone_number, secret_hash, failed_attempts, locked_until
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                u.id AS user_id,
                u.role,
                u.status,
                up.phone_number,
                ua.secret_hash,
                ua.failed_attempts,
                ua.locked_until
            FROM user_phones up
            JOIN users u      ON u.id = up.user_id
            JOIN user_auth ua ON ua.user_phone_id = up.id
            WHERE up.phone_number = %s
            LIMIT 1
            """,
            (phone_number,),
        )
        return cur.fetchone()


def bump_failed_login(conn, phone_number: str, *, max_failed: int, lock_minutes: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_auth ua
            SET
                failed_attempts = failed_attempts + 1,
                locked_until = CASE
                    WHEN failed_attempts + 1 >= %s
                    THEN (NOW() + (%s || ' minutes')::interval)
                    ELSE locked_until
                END
            FROM user_phones up
            WHERE ua.user_phone_id = up.id
              AND up.phone_number = %s
            """,
            (max_failed, lock_minutes, phone_number),
        )


def reset_failed_login(conn, phone_number: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_auth ua
            SET failed_attempts = 0,
                locked_until = NULL,
                last_login_at = NOW()
            FROM user_phones up
            WHERE ua.user_phone_id = up.id
              AND up.phone_number = %s
            """,
            (phone_number,),
        )
