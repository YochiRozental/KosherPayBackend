from fastapi import Request

from ivr.config import MAX_TIMEOUT_REPEATS
from ivr.session import session_get, session_set, session_delete


def go_back(request: Request, *keys: str, target: str = "../") -> str:
    session_delete(request, *keys)
    return f"go_to_folder={target}"


def handle_timeout_repeat(
        request,
        *,
        value: str | None,
        session_key: str,
        retry_response,
        max_repeats: int = MAX_TIMEOUT_REPEATS,
        fail_response=None,
):
    from ivr.commands import is_timeout_repeat

    if not is_timeout_repeat(value):
        session_delete(request, session_key)
        return None

    current = int(session_get(request, session_key) or "0")
    current += 1

    session_set(request, session_key, str(current))

    if current >= max_repeats:
        session_delete(request, session_key)

        if fail_response:
            return fail_response

        return "go_to_folder=../"

    return retry_response


def repeatable_read(
        request,
        *,
        value: str | None,
        session_key: str,
        prompt,
        param: str,
        min_len: int,
        max_len: int,
        read_type: str = "Digits",
        fail_folder: str = "../",
):
    from ivr.commands import read_with_back

    retry_response = read_with_back(
        prompt,
        param,
        min_len,
        max_len,
        read_type=read_type,
    )

    timeout_resp = handle_timeout_repeat(
        request,
        value=value,
        session_key=session_key,
        retry_response=retry_response,
        fail_response=f"go_to_folder={fail_folder}",
    )

    if timeout_resp:
        return timeout_resp

    if not value:
        return retry_response

    session_delete(request, session_key)
    return None
