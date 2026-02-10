from __future__ import annotations

from typing import Any

import psycopg

from auth.password import hash_secret


def _fetchone_dict(cur: psycopg.Cursor) -> dict[str, Any] | None:
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d.name for d in cur.description]
    return dict(zip(cols, row))


def get_user_id_by_phone(conn, phone_number: str) -> str | None:
    phone_number = (phone_number or "").strip()
    if not phone_number:
        return None

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id::text AS user_id
            FROM user_phones
            WHERE phone_number = %s LIMIT 1
            """,
            (phone_number,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_user_for_auth(conn, phone_number: str) -> dict[str, Any] | None:
    phone_number = (phone_number or "").strip()
    if not phone_number:
        return None

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id::text AS user_id, u.role,
                   u.status,
                   up.phone_number,
                   ua.secret_hash,
                   ua.failed_attempts,
                   ua.locked_until
            FROM user_phones up
                     JOIN users u ON u.id = up.user_id
                     JOIN user_auth ua ON ua.user_phone_id = up.id
            WHERE up.phone_number = %s LIMIT 1
            """,
            (phone_number,),
        )
        return _fetchone_dict(cur)


def bump_failed_login(conn, phone_number: str, *, max_failed: int, lock_minutes: int) -> None:
    phone_number = (phone_number or "").strip()
    if not phone_number:
        return

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_auth ua
            SET failed_attempts = failed_attempts + 1,
                locked_until    = CASE
                                      WHEN failed_attempts + 1 >= %s
                                          THEN (NOW() + (%s || ' minutes')::interval)
                                      ELSE locked_until
                    END FROM user_phones up
            WHERE ua.user_phone_id = up.id
              AND up.phone_number = %s
            """,
            (max_failed, lock_minutes, phone_number),
        )


def reset_failed_login(conn, phone_number: str) -> None:
    phone_number = (phone_number or "").strip()
    if not phone_number:
        return

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_auth ua
            SET failed_attempts = 0,
                locked_until    = NULL,
                last_login_at   = NOW() FROM user_phones up
            WHERE ua.user_phone_id = up.id
              AND up.phone_number = %s
            """,
            (phone_number,),
        )


def get_user_profile_by_id(conn, user_id: str) -> dict[str, Any] | None:
    user_id = (user_id or "").strip()
    if not user_id:
        return None

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id::text AS user_id, u.name,
                   u.role,
                   u.status,
                   up.phone_number AS phone,
                   ba.bank_number,
                   ba.branch_number,
                   ba.account_number,
                   ba.account_holder
            FROM users u
                     LEFT JOIN user_phones up
                               ON up.user_id = u.id AND up.is_primary = TRUE
                     LEFT JOIN bank_accounts ba
                               ON ba.user_id = u.id
            WHERE u.id = %s LIMIT 1
            """,
            (user_id,),
        )
        return _fetchone_dict(cur)


def update_user_profile_by_id(
        conn,
        *,
        user_id: str,
        name: str | None = None,
        phone: str | None = None,
        secret_code: str | None = None,
        bank_number: str | None = None,
        branch_number: str | None = None,
        account_number: str | None = None,
        account_holder: str | None = None,
) -> dict[str, Any]:
    user_id = (user_id or "").strip()
    if not user_id:
        raise ValueError("user_id is required")

    if name is not None:
        name = name.strip()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET name=%s, updated_at=NOW() WHERE id=%s",
                (name, user_id),
            )

    primary: dict[str, Any] | None
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text AS id, phone_number
            FROM user_phones
            WHERE user_id = %s
              AND is_primary = TRUE LIMIT 1
            """,
            (user_id,),
        )
        primary = _fetchone_dict(cur)

    if phone is not None:
        phone = phone.strip()
        if primary:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_phones SET phone_number=%s WHERE id=%s",
                    (phone, primary["id"]),
                )
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_phones (user_id, phone_number, is_primary)
                    VALUES (%s, %s, TRUE) RETURNING id::text AS id
                    """,
                    (user_id, phone),
                )
                primary = _fetchone_dict(cur)

    if secret_code is not None:
        if not primary:
            raise ValueError("No primary phone for user; cannot set secret.")
        secret_hash = hash_secret(secret_code.strip())
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_auth
                SET secret_hash=%s,
                    failed_attempts=0,
                    locked_until=NULL
                WHERE user_phone_id = %s
                """,
                (secret_hash, primary["id"]),
            )

    bank_fields_sent = any(
        x is not None for x in (bank_number, branch_number, account_number, account_holder)
    )
    if bank_fields_sent:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id
                FROM bank_accounts
                WHERE user_id = %s
                ORDER BY created_at ASC LIMIT 1
                """,
                (user_id,),
            )
            ba = _fetchone_dict(cur)

        bn = (bank_number or "").strip()
        br = (branch_number or "").strip()
        an = (account_number or "").strip()
        ah = (account_holder or "").strip()

        if ba:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE bank_accounts
                    SET bank_number=%s,
                        branch_number=%s,
                        account_number=%s,
                        account_holder=%s
                    WHERE id = %s
                    """,
                    (bn, br, an, ah, ba["id"]),
                )
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bank_accounts (user_id, bank_number, branch_number, account_number, account_holder)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, bn, br, an, ah),
                )

    updated = get_user_profile_by_id(conn, user_id)
    if not updated:
        raise ValueError("User not found after update")
    return updated
