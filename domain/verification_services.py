from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from auth.password import hash_secret, verify_secret
from repositories.verification_challenges_repo import (
    cancel_active_challenges,
    create_challenge,
    get_active_challenge_by_id,
    increment_challenge_attempts,
    mark_challenge_verified,
    mark_challenge_used,
)

RESET_SECRET_PURPOSE = "reset_secret"
FLASH_CALL_METHOD = "flash_call"

CODE_TTL_MINUTES = 5
MAX_ATTEMPTS = 5


def _normalize_phone(phone: str) -> str:
    return (phone or "").strip()


def get_user_phone_by_phone(conn, *, phone_number: str) -> dict[str, Any] | None:
    phone_number = _normalize_phone(phone_number)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT up.id::text AS user_phone_id,
                   up.user_id::text AS user_id,
                   up.phone_number,
                   up.is_primary,
                   u.status AS user_status
            FROM user_phones up
            JOIN users u ON u.id = up.user_id
            WHERE up.phone_number = %s
              AND u.deleted_at IS NULL
            LIMIT 1
            """,
            (phone_number,),
        )

        row = cur.fetchone()

    if not row:
        return None

    return {
        "user_phone_id": row["user_phone_id"],
        "user_id": row["user_id"],
        "phone_number": row["phone_number"],
        "is_primary": row["is_primary"],
        "user_status": row["user_status"],
    }


def start_reset_secret_challenge(
        conn,
        *,
        phone_number: str,
        channel: str,
        verify_code: str,
        provider: str | None = "yemot",
        provider_call_id: str | None = None,
) -> dict[str, Any]:
    """
    יוצר בקשת שחזור קוד אחרי ש-Flash Call כבר נשלח
    וקיבלנו מימות המשיח verifyCode.
    """

    phone_number = _normalize_phone(phone_number)

    if channel not in {"ivr", "web"}:
        return {"success": False, "message": "ערוץ לא תקין"}

    if not phone_number:
        return {"success": False, "message": "חסר מספר טלפון"}

    if not verify_code or not verify_code.isdigit():
        return {"success": False, "message": "קוד אימות לא תקין"}

    user_phone = get_user_phone_by_phone(conn, phone_number=phone_number)

    if not user_phone:
        return {"success": False, "message": "מספר הטלפון אינו קיים במערכת"}

    if user_phone["user_status"] != "active":
        return {"success": False, "message": "החשבון אינו פעיל"}

    cancel_active_challenges(
        conn,
        user_id=user_phone["user_id"],
        purpose=RESET_SECRET_PURPOSE,
    )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES)

    challenge = create_challenge(
        conn,
        user_id=user_phone["user_id"],
        user_phone_id=user_phone["user_phone_id"],
        purpose=RESET_SECRET_PURPOSE,
        channel=channel,
        code_hash=hash_secret(verify_code),
        expires_at=expires_at,
        provider=provider,
        provider_call_id=provider_call_id,
    )

    return {
        "success": True,
        "message": "נשלחה שיחת אימות",
        "challenge_id": str(challenge["id"]),
        "expires_in_minutes": CODE_TTL_MINUTES,
    }


def verify_reset_secret_challenge(
        conn,
        *,
        challenge_id: str,
        code: str,
) -> dict[str, Any]:
    """
    בודק את 4 הספרות שהמשתמש הקיש.
    אם תקין - מסמן verified_at.
    """

    code = (code or "").strip()

    if not challenge_id:
        return {"success": False, "message": "חסר מזהה אימות"}

    if not code or not code.isdigit():
        return {"success": False, "message": "קוד האימות לא תקין"}

    challenge = get_active_challenge_by_id(conn, challenge_id=challenge_id)

    if not challenge:
        return {"success": False, "message": "קוד האימות פג תוקף או אינו קיים"}

    if challenge["attempts"] >= challenge["max_attempts"]:
        mark_challenge_used(conn, challenge_id=challenge_id)
        return {"success": False, "message": "בוצעו יותר מדי ניסיונות"}

    if not verify_secret(code, challenge["code_hash"]):
        increment_challenge_attempts(conn, challenge_id=challenge_id)
        return {"success": False, "message": "קוד האימות שגוי"}

    mark_challenge_verified(conn, challenge_id=challenge_id)

    return {
        "success": True,
        "message": "האימות הצליח",
        "challenge_id": challenge_id,
    }


def reset_secret_after_verification(
        conn,
        *,
        challenge_id: str,
        new_secret: str,
        confirm_secret: str | None = None,
) -> dict[str, Any]:
    """
    מעדכן קוד סודי חדש רק אחרי שה-challenge אומת.
    """

    new_secret = (new_secret or "").strip()

    if confirm_secret is not None:
        confirm_secret = confirm_secret.strip()
        if new_secret != confirm_secret:
            return {"success": False, "message": "הקודים אינם תואמים"}

    if not new_secret or not new_secret.isdigit() or len(new_secret) != 6:
        return {"success": False, "message": "הקוד החדש חייב להכיל 6 ספרות"}

    challenge = get_active_challenge_by_id(conn, challenge_id=challenge_id)

    if not challenge:
        return {"success": False, "message": "בקשת האימות אינה קיימת או פגה"}

    if not challenge.get("verified_at"):
        return {"success": False, "message": "יש להשלים אימות לפני החלפת קוד"}

    new_secret_hash = hash_secret(new_secret)

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_auth
            SET secret_hash = %s,
                failed_attempts = 0,
                locked_until = NULL
            WHERE user_phone_id = %s
            """,
            (new_secret_hash, challenge["user_phone_id"]),
        )

    mark_challenge_used(conn, challenge_id=challenge_id)

    return {
        "success": True,
        "message": "הקוד הסודי עודכן בהצלחה",
    }
