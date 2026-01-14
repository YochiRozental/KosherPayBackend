from __future__ import annotations
from datetime import datetime, timezone
import os

from auth.password import verify_secret
from auth.jwt_utils import create_access_token, create_refresh_token
from repositories.users_repo import get_user_for_auth, bump_failed_login, reset_failed_login

AUTH_MAX_FAILED = int(os.environ.get("AUTH_MAX_FAILED", "5"))
AUTH_LOCK_MINUTES = int(os.environ.get("AUTH_LOCK_MINUTES", "15"))

def authenticate_user(conn, phone_number: str, secret_code: str) -> dict:
    phone_number = (phone_number or "").strip()
    secret_code = (secret_code or "").strip()

    row = get_user_for_auth(conn, phone_number)
    if not row:
        return {"success": False, "message": "פרטי התחברות שגויים"}

    if row.get("status") != "active":
        return {"success": False, "message": "המשתמש לא פעיל"}

    locked_until = row.get("locked_until")
    if locked_until and locked_until > datetime.now(timezone.utc):
        return {"success": False, "message": "החשבון נעול זמנית עקב ניסיונות כושלים"}

    if not verify_secret(secret_code, row["secret_hash"]):
        bump_failed_login(
            conn,
            phone_number,
            max_failed=AUTH_MAX_FAILED,
            lock_minutes=AUTH_LOCK_MINUTES,
        )
        return {"success": False, "message": "פרטי התחברות שגויים"}

    reset_failed_login(conn, phone_number)

    user_id = str(row["user_id"])
    role = row["role"]

    return {
        "success": True,
        "access_token": create_access_token(
            user_id=user_id,
            role=role,
            phone_number=phone_number,  # עדיין נשמר בטוקן לנוחות; אבל הדומיין עובד עם user_id
        ),
        "refresh_token": create_refresh_token(user_id=user_id),
        "user": {
            "id": user_id,
            "role": role,
            "phone": phone_number,
        },
    }
