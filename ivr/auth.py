import requests
from fastapi import Request

from domain.verification_services import (
    get_reset_secret_target,
    reset_secret_after_verification,
    start_reset_secret_challenge,
    verify_reset_secret_challenge,
)
from integrations.yemot_api import send_flash_call
from ivr.commands import yemot_read, yemot_say
from ivr.prompts import yemot_error, yemot_prompt
from ivr.session import session_delete, session_get, session_set

FORGOT_SECRET_SESSION_KEYS = (
    "new_secret",
    "forgot_secret_code",
    "forgot_secret_challenge_id",
    "secret_code",
)


def require_auth(request: Request) -> tuple[str | None, str | None]:
    user_id = session_get(request, "user_id")
    if not user_id:
        return None, yemot_say("יש להתחבר תחילה", go_to_folder="/")
    return user_id, None


def forgot_secret_ask_verify_code() -> str:
    return yemot_read(
        yemot_prompt("FORGOT_SECRET_ENTER_VERIFY_CODE"),
        "forgot_secret_code",
        4,
        4,
        read_type="Digits",
        confirm=False,
    )


def forgot_secret_ask_new_secret() -> str:
    return yemot_read(
        yemot_prompt("FORGOT_SECRET_ENTER_NEW_SECRET"),
        "new_secret",
        6,
        6,
        read_type="Digits",
        confirm=False,
    )


def forgot_secret_start(
        conn,
        request: Request,
        phone_number: str,
) -> str:
    target = get_reset_secret_target(
        conn,
        phone_number=phone_number,
    )

    if not target.get("success"):
        return yemot_error(
            "FORGOT_SECRET_START_FAILED",
            go_to_folder="/",
        )

    try:
        flash_call = send_flash_call(
            phone_number=target["primary_phone_number"],
        )
    except (requests.RequestException, RuntimeError, ValueError):
        return yemot_error(
            "FORGOT_SECRET_CALL_FAILED",
            go_to_folder="/",
        )

    if not flash_call.get("verify_code"):
        return yemot_error(
            "FORGOT_SECRET_CALL_FAILED",
            go_to_folder="/",
        )

    result = start_reset_secret_challenge(
        conn,
        phone_number=phone_number,
        channel="ivr",
        verify_code=flash_call["verify_code"],
        provider="yemot",
        provider_call_id=flash_call.get("provider_call_id"),
    )

    if not result.get("success"):
        return yemot_error(
            "FORGOT_SECRET_START_FAILED",
            go_to_folder="/",
        )

    session_set(
        request,
        "forgot_secret_challenge_id",
        result["challenge_id"],
    )

    return forgot_secret_ask_verify_code()


def forgot_secret_verify(conn, request: Request, code: str) -> str:
    challenge_id = session_get(request, "forgot_secret_challenge_id")

    if not challenge_id:
        return yemot_error("FORGOT_SECRET_EXPIRED", go_to_folder="/")

    result = verify_reset_secret_challenge(
        conn,
        challenge_id=challenge_id,
        code=code,
    )

    session_delete(request, "forgot_secret_code")

    if not result.get("success"):
        return yemot_error("FORGOT_SECRET_WRONG_CODE", go_to_folder="/")

    return forgot_secret_ask_new_secret()


def forgot_secret_reset(conn, request: Request, new_secret: str) -> str:
    challenge_id = session_get(request, "forgot_secret_challenge_id")

    if not challenge_id:
        return yemot_error("FORGOT_SECRET_EXPIRED", go_to_folder="/")

    result = reset_secret_after_verification(
        conn,
        challenge_id=challenge_id,
        new_secret=new_secret,
    )

    session_delete(request, *FORGOT_SECRET_SESSION_KEYS)

    if not result.get("success"):
        return yemot_error("FORGOT_SECRET_RESET_FAILED", go_to_folder="/")

    return yemot_say(
        yemot_prompt("FORGOT_SECRET_RESET_SUCCESS_LOGIN"),
        go_to_folder="/",
    )
