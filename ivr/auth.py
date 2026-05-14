from fastapi import Request

from ivr.commands import yemot_say
from ivr.session import session_get


def require_auth(request: Request) -> tuple[str | None, str | None]:
    user_id = session_get(request, "user_id")
    if not user_id:
        return None, yemot_say("יש להתחבר תחילה", go_to_folder="/")
    return user_id, None
