from __future__ import annotations

import psycopg2
import psycopg2.extras

from auth.password import hash_secret
from repositories.users_repo import (
    get_user_id_by_phone,
)

def open_account(
    conn,
    *,
    phone_number: str,
    secret_code: str,
    name: str,
    bank_number: str,
    branch_number: str,
    account_number: str,
) -> dict:
    phone_number = (phone_number or "").strip()
    name = (name or "").strip()

    existing = get_user_id_by_phone(conn, phone_number)
    if existing:
        return {
            "success": False,
            "message": "מספר טלפון זה כבר קיים במערכת",
            "error_code": "PHONE_ALREADY_EXISTS",
        }

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1) users
            cur.execute(
                """
                INSERT INTO users (name, role, status)
                VALUES (%s, 'user', 'active')
                RETURNING id
                """,
                (name,),
            )
            user_id = cur.fetchone()["id"]

            # 2) user_phones
            cur.execute(
                """
                INSERT INTO user_phones (user_id, phone_number, is_primary)
                VALUES (%s, %s, TRUE)
                RETURNING id
                """,
                (user_id, phone_number),
            )
            user_phone_id = cur.fetchone()["id"]

            # 3) user_auth
            secret_hash = hash_secret(secret_code)
            cur.execute(
                """
                INSERT INTO user_auth (user_phone_id, secret_hash, failed_attempts, locked_until)
                VALUES (%s, %s, 0, NULL)
                """,
                (user_phone_id, secret_hash),
            )

            # 4) wallets
            cur.execute(
                """
                INSERT INTO wallets (user_id, current_balance, currency)
                VALUES (%s, 0, 'ILS')
                """,
                (user_id,),
            )

            # 5) bank_accounts
            cur.execute(
                """
                INSERT INTO bank_accounts (
                    user_id,
                    bank_number,
                    branch_number,
                    account_number,
                    account_holder
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user_id,
                    bank_number,
                    branch_number,
                    account_number,
                    name,
                ),
            )
            bank_account_id = cur.fetchone()["id"]

        return {
            "success": True,
            "message": "המשתמש נרשם בהצלחה",
            "user_id": str(user_id),
            "bank_account_id": str(bank_account_id),
        }

    except psycopg2.errors.UniqueViolation:
        return {
            "success": False,
            "message": "מספר טלפון זה כבר קיים במערכת",
            "error_code": "PHONE_ALREADY_EXISTS",
        }
