from __future__ import annotations
import psycopg2.extras
from auth.password import hash_secret

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

def get_user_profile_by_id(conn, user_id: str) -> dict | None:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                u.id AS user_id,
                u.name,
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
            WHERE u.id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return cur.fetchone()

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
) -> dict:
    # 1) update name
    if name is not None:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET name=%s, updated_at=NOW() WHERE id=%s",
                (name.strip(), user_id),
            )

    # 2) get primary phone row
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, phone_number
            FROM user_phones
            WHERE user_id=%s AND is_primary=TRUE
            LIMIT 1
            """,
            (user_id,),
        )
        primary = cur.fetchone()

    # 3) update / insert phone
    if phone is not None:
        if primary:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_phones SET phone_number=%s WHERE id=%s",
                    (phone.strip(), primary["id"]),
                )
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_phones (user_id, phone_number, is_primary)
                    VALUES (%s, %s, TRUE)
                    RETURNING id
                    """,
                    (user_id, phone.strip()),
                )
                primary = {"id": cur.fetchone()[0]}

    # 4) update password if provided
    if secret_code is not None:
        if not primary:
            raise ValueError("No primary phone for user; cannot set secret.")
        secret_hash = hash_secret(secret_code)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE user_auth
                SET secret_hash=%s,
                    failed_attempts=0,
                    locked_until=NULL
                WHERE user_phone_id=%s
                """,
                (secret_hash, primary["id"]),
            )

    # 5) bank account upsert by user_id
    bank_fields_sent = any(x is not None for x in [bank_number, branch_number, account_number, account_holder])
    if bank_fields_sent:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id FROM bank_accounts WHERE user_id=%s ORDER BY created_at ASC LIMIT 1", (user_id,))
            ba = cur.fetchone()

        if ba:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE bank_accounts
                    SET bank_number=%s,
                        branch_number=%s,
                        account_number=%s,
                        account_holder=%s
                    WHERE id=%s
                    """,
                    (
                        (bank_number or "").strip(),
                        (branch_number or "").strip(),
                        (account_number or "").strip(),
                        (account_holder or "").strip(),
                        ba["id"],
                    ),
                )
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bank_accounts (user_id, bank_number, branch_number, account_number, account_holder)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        (bank_number or "").strip(),
                        (branch_number or "").strip(),
                        (account_number or "").strip(),
                        (account_holder or "").strip(),
                    ),
                )

    updated = get_user_profile_by_id(conn, user_id)
    if not updated:
        raise ValueError("User not found after update")
    return updated
