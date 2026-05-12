from __future__ import annotations

from auth.password import hash_secret
from repositories.account_creation_repo import (
    create_user,
    create_user_phone,
    create_user_auth,
    create_wallet,
    create_bank_account,
    is_phone_unique_violation,
)
from repositories.bank_branches_repo import (
    get_active_bank_branch,
    normalize_account_number,
    normalize_bank_code,
    normalize_branch_code,
)
from repositories.users_repo import get_user_id_by_phone


def _normalize_phone(phone: str) -> str:
    return (phone or "").strip()


def _normalize_additional_phones(phone_number: str, additional_phones: list[str] | None) -> list[str]:
    primary_phone = _normalize_phone(phone_number)
    seen = {primary_phone}
    out: list[str] = []

    for phone in additional_phones or []:
        phone = _normalize_phone(phone)

        if not phone or phone in seen:
            continue

        seen.add(phone)
        out.append(phone)

    return out


def open_account(
        conn,
        *,
        phone_number: str,
        secret_code: str,
        name: str,
        bank_number: str,
        branch_number: str,
        account_number: str,
        additional_phones: list[str] | None = None,
) -> dict:
    phone_number = _normalize_phone(phone_number)
    name = (name or "").strip()
    additional_phones = _normalize_additional_phones(phone_number, additional_phones)

    if not phone_number or not secret_code or not name:
        return {"success": False, "message": "חסרים פרטים חובה"}

    try:
        bank_number = normalize_bank_code(bank_number)
        branch_number = normalize_branch_code(branch_number)
        account_number = normalize_account_number(account_number)

    except ValueError:
        return {
            "success": False,
            "message": "פרטי חשבון הבנק אינם תקינים",
            "error_code": "INVALID_BANK_ACCOUNT_DETAILS",
        }

    bank_branch = get_active_bank_branch(
        conn,
        bank_number=bank_number,
        branch_number=branch_number,
    )

    if not bank_branch:
        return {
            "success": False,
            "message": "בנק או סניף לא קיימים או שאינם פעילים",
            "error_code": "INVALID_BANK_BRANCH",
        }

    all_phones = [phone_number, *additional_phones]

    for phone in all_phones:
        existing = get_user_id_by_phone(conn, phone)

        if existing:
            return {
                "success": False,
                "message": "מספר טלפון זה כבר קיים במערכת",
                "error_code": "PHONE_ALREADY_EXISTS",
                "phone_number": phone,
            }

    try:
        user_id = create_user(conn, name=name)

        secret_hash = hash_secret(secret_code)

        user_phone_id = create_user_phone(
            conn,
            user_id=user_id,
            phone_number=phone_number,
            is_primary=True,
        )

        create_user_auth(
            conn,
            user_phone_id=user_phone_id,
            secret_hash=secret_hash,
        )

        for extra_phone in additional_phones:
            extra_phone_id = create_user_phone(
                conn,
                user_id=user_id,
                phone_number=extra_phone,
                is_primary=False,
            )

            create_user_auth(
                conn,
                user_phone_id=extra_phone_id,
                secret_hash=secret_hash,
            )

        create_wallet(conn, user_id=user_id, currency="ILS")

        bank_account_id = create_bank_account(
            conn,
            user_id=user_id,
            bank_number=bank_number,
            branch_number=branch_number,
            account_number=account_number,
            account_holder=name,
            bank_branch_id=bank_branch["id"],
            verification_status="pending_verification",
        )

        conn.commit()

        return {
            "success": True,
            "message": "המשתמש נרשם בהצלחה",
            "user_id": str(user_id),
            "bank_account_id": str(bank_account_id),
        }

    except Exception as e:
        conn.rollback()

        if is_phone_unique_violation(e):
            return {
                "success": False,
                "message": "מספר טלפון זה כבר קיים במערכת",
                "error_code": "PHONE_ALREADY_EXISTS",
            }

        return {
            "success": False,
            "message": "שגיאה במערכת",
            "error": str(e),
        }
