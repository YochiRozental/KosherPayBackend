from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Request

from db.redis_client import get_redis
from ivr.config import SESSION_TTL_MIN

ALLOWED_KEYS = {
    "bank_number",
    "branch_number",
    "account_number",
    "name",
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

}


def _key(call_id: str) -> str:
    return f"yemot:call:{call_id}"


def init_yemot_session(request: Request) -> dict[str, str]:
    r = get_redis()

    call_id = request.query_params.get("ApiCallId")
    if not call_id:
        request.state.yemot_call_id = None
        request.state.yemot_session = {}
        return request.state.yemot_session

    key = _key(call_id)

    session: dict[str, str] = r.hgetall(key) or {}

    qs = str(request.url.query or "")
    if qs:
        for part in qs.split("&"):
            if "=" not in part:
                continue
            pkey, value = part.split("=", 1)
            if pkey in ALLOWED_KEYS:
                session[pkey] = value
                r.hset(key, mapping={pkey: value})

    now = datetime.now(timezone.utc).isoformat()
    session["__last_seen"] = now
    r.hset(key, mapping={"__last_seen": now})
    r.expire(key, SESSION_TTL_MIN * 60)

    request.state.yemot_call_id = call_id
    request.state.yemot_session = session
    return session


def get_session(request: Request) -> dict[str, str]:
    return getattr(request.state, "yemot_session", {})


def session_get(request: Request, key: str) -> str | None:
    session = get_session(request)
    v = session.get(key)
    return v if v else None


def session_set(request: Request, key: str, value: str) -> None:
    call_id = getattr(request.state, "yemot_call_id", None)
    if not call_id:
        return

    r = get_redis()
    redis_key = _key(call_id)

    r.hset(redis_key, key, value)
    r.expire(redis_key, SESSION_TTL_MIN * 60)

    session = get_session(request)
    session[key] = value


def session_delete(request: Request, *keys: str) -> None:
    call_id = getattr(request.state, "yemot_call_id", None)
    if not call_id or not keys:
        return

    r = get_redis()
    redis_key = _key(call_id)

    r.hdel(redis_key, *keys)

    session = get_session(request)
    for k in keys:
        session.pop(k, None)
