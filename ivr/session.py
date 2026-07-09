from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Request

from db.redis_client import get_redis
from ivr.config import SESSION_TTL_MIN

ALLOWED_KEYS = {
    "secret_code",
    "forgot_secret_code",
    "new_secret",
    "forgot_secret_challenge_id",

    "user_id",
    "authenticated",
    "phone",
    "welcome_played",
    "user_name",

    "bank_number",
    "branch_number",
    "account_number",
    "name",
    "name_choice",
    "name_recording",
    "name_recording_path",
    "add_phones_choice",
    "extra_phone_count",
    "extra_phone_i",
    "extra_phones",

    "recipient_phone",
    "amount",
    "amount_t",
    "amount_d",
    "amount_w",
    "amount_deposit",
    "amount_withdraw",
    "to_phone",
    "amount_transfer",
    "pay_req_phone",
    "pay_req_amount",

    "req_i",
    "req_id",
    "choice",
    "last_handled_req_id",
    "last_handled_choice",
    "sent_next_choice",
    "sent_req_offset",

    "history_offset",
    "history_choice",
    "history_next_choice",
    "history_start_date",
    "history_end_date",
    "history_range_start_iso",
    "history_range_end_iso",

    "edit_idx",
    "edit_choice",
    "new_name",
    "new_phone",
    "new_secret_code",
    "new_bank_number",
    "new_branch_number",
    "new_account_number",
    "new_account_holder",
}


def _session_id(request: Request) -> str | None:
    return request.query_params.get("ApiCallId")


def _key(session_id: str) -> str:
    return f"yemot:call:{session_id}"


def _decode_redis_hash(raw: dict) -> dict[str, str]:
    return {
        (k.decode() if isinstance(k, bytes) else str(k)): (
            v.decode() if isinstance(v, bytes) else str(v)
        )
        for k, v in raw.items()
    }


def init_yemot_session(request: Request) -> dict[str, str]:
    r = get_redis()

    session_id = _session_id(request)
    if not session_id:
        request.state.yemot_call_id = None
        request.state.yemot_session = {}
        return request.state.yemot_session

    redis_key = _key(session_id)

    raw_session = r.hgetall(redis_key) or {}
    session = _decode_redis_hash(raw_session)

    for pkey, value in request.query_params.multi_items():
        if pkey in ALLOWED_KEYS:
            session[pkey] = value
            r.hset(redis_key, mapping={pkey: value})

    now = datetime.now(timezone.utc).isoformat()
    session["__last_seen"] = now

    r.hset(redis_key, mapping={"__last_seen": now})
    r.expire(redis_key, SESSION_TTL_MIN * 60)

    request.state.yemot_call_id = session_id
    request.state.yemot_session = session
    return session


def get_session(request: Request) -> dict[str, str]:
    return getattr(request.state, "yemot_session", {})


def session_get(request: Request, key: str) -> str | None:
    value = get_session(request).get(key)
    return value if value else None


def session_set(request: Request, key: str, value: str) -> None:
    session_id = getattr(request.state, "yemot_call_id", None)
    if not session_id:
        return

    r = get_redis()
    redis_key = _key(session_id)

    value = str(value)

    r.hset(redis_key, key, value)
    r.expire(redis_key, SESSION_TTL_MIN * 60)

    get_session(request)[key] = value


def session_delete(request: Request, *keys: str) -> None:
    session_id = getattr(request.state, "yemot_call_id", None)
    if not session_id or not keys:
        return

    r = get_redis()
    redis_key = _key(session_id)

    r.hdel(redis_key, *keys)

    session = get_session(request)
    for key in keys:
        session.pop(key, None)
