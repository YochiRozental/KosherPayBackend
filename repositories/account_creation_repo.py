from __future__ import annotations

from uuid import UUID

from psycopg import errors


def create_user(conn, *, name: str) -> UUID:
    name = (name or "").strip()
    if not name:
        raise ValueError("name is required")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (name, role, status)
            VALUES (%s, 'user', 'active') RETURNING id
            """,
            (name,),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Failed to create user")
        return row["id"]


def create_user_phone(conn, *, user_id: UUID, phone_number: str, is_primary: bool = True) -> UUID:
    phone_number = (phone_number or "").strip()
    if not phone_number:
        raise ValueError("phone_number is required")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_phones (user_id, phone_number, is_primary)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (user_id, phone_number, is_primary),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Failed to create user phone")
        return row["id"]


def create_user_auth(
        conn,
        *,
        user_phone_id: UUID,
        secret_hash: str,
) -> None:
    secret_hash = (secret_hash or "").strip()
    if not secret_hash:
        raise ValueError("secret_hash is required")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_auth (user_phone_id, secret_hash, failed_attempts, locked_until)
            VALUES (%s, %s, 0, NULL)
            """,
            (user_phone_id, secret_hash),
        )


def create_wallet(
        conn,
        *,
        user_id: UUID,
        currency: str = "ILS",
) -> None:
    currency = (currency or "").strip() or "ILS"

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
        bank_branch_id: int,
        verification_status: str = "pending_verification",
) -> UUID:
    bank_number = (bank_number or "").strip()
    branch_number = (branch_number or "").strip()
    account_number = (account_number or "").strip()
    account_holder = (account_holder or "").strip()

    if not all([bank_number, branch_number, account_number, account_holder]):
        raise ValueError("All bank account fields are required")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bank_accounts (
                user_id,
                bank_number,
                branch_number,
                account_number,
                account_holder,
                bank_branch_id,
                verification_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                bank_number,
                branch_number,
                account_number,
                account_holder,
                bank_branch_id,
                verification_status,
            ),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Failed to create bank account")
        return row["id"]


def is_phone_unique_violation(err: Exception) -> bool:
    return isinstance(err, errors.UniqueViolation)
