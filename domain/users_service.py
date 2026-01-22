from __future__ import annotations

import re
from typing import Any, Mapping

import psycopg2

from repositories.users_repo import (
    get_user_profile_by_id,
    update_user_profile_by_id,
)

_PHONE_RE = re.compile(r"^0\d{8,9}$")


def _to_user_me(profile: Mapping[str, Any]) -> dict[str, Any]:
    """
    ממפה רשומת פרופיל מה-DB (dict) למבנה אחיד של user ל-API.
    """
    return {
        "id": str(profile.get("user_id") or ""),
        "name": profile.get("name") or "",
        "role": profile.get("role") or "user",
        "phone": profile.get("phone") or "",
        "bankAccount": {
            "bankNumber": profile.get("bank_number") or "",
            "branchNumber": profile.get("branch_number") or "",
            "accountNumber": profile.get("account_number") or "",
            "accountHolder": profile.get("account_holder") or "",
        },
    }


def get_me(conn, *, user_id: str) -> dict[str, Any]:
    """
    מחזיר פרופיל משתמש מלא (שם/תפקיד/טלפון/בנק) לפי user_id.
    """
    profile = get_user_profile_by_id(conn, user_id)
    if not profile:
        return {"success": False, "message": "משתמש לא נמצא"}

    return {
        "success": True,
        "user": _to_user_me(profile),
    }


def update_me(
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
    """
        Update authenticated user profile.

        Behavior:
        - Only provided fields are updated (None values are ignored)
        - Performs basic validation before persisting data

        Security:
        - Password is re-hashed before storage
        - Does not expose internal errors to client
        """
    # Normalize
    name = name.strip() if isinstance(name, str) else None
    phone = phone.strip() if isinstance(phone, str) else None
    secret_code = secret_code.strip() if isinstance(secret_code, str) else None

    bank_number = bank_number.strip() if isinstance(bank_number, str) else None
    branch_number = branch_number.strip() if isinstance(branch_number, str) else None
    account_number = account_number.strip() if isinstance(account_number, str) else None
    account_holder = account_holder.strip() if isinstance(account_holder, str) else None

    # Validation
    if name is not None and not name:
        return {"success": False, "message": "שם לא תקין"}

    if phone is not None and not _PHONE_RE.match(phone):
        return {"success": False, "message": "טלפון לא תקין"}

    if secret_code is not None and len(secret_code) < 4:
        return {"success": False, "message": "קוד סודי קצר מדי"}

    if bank_number is not None and not bank_number.isdigit():
        return {"success": False, "message": "מספר בנק לא תקין"}

    if branch_number is not None and not branch_number.isdigit():
        return {"success": False, "message": "מספר סניף לא תקין"}

    if account_number is not None and not account_number.isdigit():
        return {"success": False, "message": "מספר חשבון לא תקין"}

    if account_holder is not None and not account_holder:
        return {"success": False, "message": "שם בעל חשבון לא תקין"}

    try:
        updated = update_user_profile_by_id(
            conn,
            user_id=user_id,
            name=name,
            phone=phone,
            secret_code=secret_code,
            bank_number=bank_number,
            branch_number=branch_number,
            account_number=account_number,
            account_holder=account_holder,
        )
    except ValueError:
        return {"success": False, "message": "נתונים לא תקינים"}
    except psycopg2.Error:
        return {"success": False, "message": "שגיאה בשמירת הנתונים"}

    return {
        "success": True,
        "message": "הפרטים עודכנו",
        "user": _to_user_me(updated),
    }
