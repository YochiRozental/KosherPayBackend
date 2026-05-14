from urllib.parse import unquote_plus

from fastapi import Request

from ivr.session import session_get


def decode_yemot_value(value: str | None) -> str:
    if not value:
        return ""
    return unquote_plus(str(value)).strip()


def get_param(request: Request, key: str) -> str:
    return decode_yemot_value(request.query_params.get(key))


def get_param_or_session(request: Request, key: str) -> str:
    return decode_yemot_value(
        get_param(request, key) or session_get(request, key)
    )


def parse_amount(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
