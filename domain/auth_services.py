from __future__ import annotations

import os
from datetime import datetime, timezone

from auth.jwt_utils import create_access_token, create_refresh_token
from auth.password import verify_secret
from repositories.users_repo import get_user_for_auth, bump_failed_login, reset_failed_login

AUTH_MAX_FAILED = int(os.environ.get("AUTH_MAX_FAILED", "5"))
AUTH_LOCK_MINUTES = int(os.environ.get("AUTH_LOCK_MINUTES", "15"))


def _as_utc_aware(dt: datetime) -> datetime:
    # אם הגיע naive (בלי tzinfo) – נתייחס אליו כ-UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    # אם הגיע עם tzinfo – נמיר ל-UTC
    return dt.astimezone(timezone.utc)


def authenticate_user(conn, phone_number: str, secret_code: str) -> dict:
    phone_number = (phone_number or "").strip()
    secret_code = (secret_code or "").strip()

    row = get_user_for_auth(conn, phone_number)
    if not row:
        return {
            "success": False,
            "message": "פרטי התחברות שגויים",
        }

    locked_until = row.get("locked_until")

    if isinstance(locked_until, datetime):
        locked_until = _as_utc_aware(locked_until)

        if locked_until > datetime.now(timezone.utc):
            return {
                "success": False,
                "message": "החשבון נעול זמנית עקב ניסיונות כושלים",
            }

    if not verify_secret(secret_code, row["secret_hash"]):
        bump_failed_login(
            conn,
            phone_number,
            max_failed=AUTH_MAX_FAILED,
            lock_minutes=AUTH_LOCK_MINUTES,
        )
        return {
            "success": False,
            "message": "פרטי התחברות שגויים",
        }

    # הקוד הסודי נכון, לכן אפשר לחשוף למשתמש את מצב החשבון
    status = row["status"]

    if status == "pending_approval":
        return {
            "success": False,
            "message": "החשבון ממתין לאישור מנהל",
            "error_code": "ACCOUNT_PENDING_APPROVAL",
        }

    if status == "rejected":
        return {
            "success": False,
            "message": "החשבון לא אושר",
            "error_code": "ACCOUNT_REJECTED",
        }

    if status == "blocked":
        return {
            "success": False,
            "message": "החשבון חסום",
            "error_code": "ACCOUNT_BLOCKED",
        }

    if status != "active":
        return {
            "success": False,
            "message": "לא ניתן להתחבר לחשבון",
            "error_code": "ACCOUNT_NOT_ACTIVE",
        }

    reset_failed_login(conn, phone_number)

    user_id = str(row["user_id"])
    role = row["role"]

    return {
        "success": True,
        "access_token": create_access_token(
            user_id=user_id,
            role=role,
            phone_number=phone_number,
        ),
        "refresh_token": create_refresh_token(
            user_id=user_id,
        ),
        "user": {
            "id": user_id,
            "role": role,
            "phone": phone_number,
        },
    }
