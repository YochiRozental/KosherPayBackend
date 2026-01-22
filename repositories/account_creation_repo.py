from __future__ import annotations

from uuid import UUID

import psycopg2
import psycopg2.extras


def create_user(conn, *, name: str) -> UUID:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO users (name, role, status)
            VALUES (%s, 'user', 'active')
            RETURNING id
            """,
            (name,),
        )
        return cur.fetchone()["id"]  # UUID


def create_user_phone(
    conn, *, user_id: UUID, phone_number: str, is_primary: bool = True
) -> UUID:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO user_phones (user_id, phone_number, is_primary)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (user_id, phone_number, is_primary),
        )
        return cur.fetchone()["id"]  # UUID


def create_user_auth(conn, *, user_phone_id: UUID, secret_hash: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_auth (user_phone_id, secret_hash, failed_attempts, locked_until)
            VALUES (%s, %s, 0, NULL)
            """,
            (user_phone_id, secret_hash),
        )


def create_wallet(conn, *, user_id: UUID, currency: str = "ILS") -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO wallets (user_id, current_balance, currency)
            VALUES (%s, 0, %s)
            """,
            (user_id, currency),
        )


def create_bank_account(
    conn,
    *,
    user_id: UUID,
    bank_number: str,
    branch_number: str,
    account_number: str,
    account_holder: str,
) -> UUID:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            (user_id, bank_number, branch_number, account_number, account_holder),
        )
        return cur.fetchone()["id"]  # UUID


def is_phone_unique_violation(err: Exception) -> bool:
    return isinstance(err, psycopg2.errors.UniqueViolation)
