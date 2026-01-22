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
from repositories.users_repo import get_user_id_by_phone


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

    if not phone_number or not secret_code or not name:
        return {"success": False, "message": "חסרים פרטים חובה"}

    existing = get_user_id_by_phone(conn, phone_number)
    if existing:
        return {
            "success": False,
            "message": "מספר טלפון זה כבר קיים במערכת",
            "error_code": "PHONE_ALREADY_EXISTS",
        }

    try:
        # חשוב: טרנזקציה אחת לכל תהליך ההרשמה
        with conn:
            user_id = create_user(conn, name=name)

            user_phone_id = create_user_phone(
                conn,
                user_id=user_id,
                phone_number=phone_number,
                is_primary=True,
            )

            secret_hash = hash_secret(secret_code)
            create_user_auth(conn, user_phone_id=user_phone_id, secret_hash=secret_hash)

            create_wallet(conn, user_id=user_id, currency="ILS")

            bank_account_id = create_bank_account(
                conn,
                user_id=user_id,
                bank_number=bank_number,
                branch_number=branch_number,
                account_number=account_number,
                account_holder=name,
            )

        return {
            "success": True,
            "message": "המשתמש נרשם בהצלחה",
            "user_id": str(user_id),
            "bank_account_id": str(bank_account_id),
        }

    except Exception as e:
        # אם זה ייחודיות על טלפון – נחזיר הודעה ידידותית
        if is_phone_unique_violation(e):
            return {
                "success": False,
                "message": "מספר טלפון זה כבר קיים במערכת",
                "error_code": "PHONE_ALREADY_EXISTS",
            }
        # אחרת שגיאה כללית
        return {
            "success": False,
            "message": "שגיאה במערכת",
            "error": str(e),
        }
