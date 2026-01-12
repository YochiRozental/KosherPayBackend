# # yemot_session.py
# from flask import request, g
#
# # חנות SESSION בזיכרון (רצוי ברדיס/DB בפרודקשן)
# SESSION_STORE: dict[str, dict[str, str]] = {}
#
# def init_yemot_session():
#     """
#     מקביל ל:
#     session_id($_GET['ApiCallId']);
#     session_start();
#     + הכנסת הפרמטר האחרון ל-SESSION
#     לפי הדוגמה בפורום.
#     """
#     call_id = request.args.get("ApiCallId")
#
#     if not call_id:
#         # אין שיחה - אין SESSION
#         g.yemot_call_id = None
#         g.yemot_session = {}
#         return
#
#     # יוצרים/טוענים SESSION לשיחה
#     session = SESSION_STORE.setdefault(call_id, {})
#
#     # בדיוק כמו ב-PHP:
#     # $QUERY_STRING = $_SERVER['QUERY_STRING'];
#     # $last_param = substr($QUERY_STRING, strrpos($QUERY_STRING, '&') + 1);
#     # $param = explode('=', $last_param);
#     # $_SESSION[$param[0]] = $_GET[$param[0]];
#     qs = (request.query_string or b"").decode("utf-8")
#     if qs:
#         last_param = qs.split("&")[-1]
#         if "=" in last_param:
#             key, value = last_param.split("=", 1)
#             # שומרים רק את הפרמטר האחרון ב-SESSION
#             session[key] = value
#
#     g.yemot_call_id = call_id
#     g.yemot_session = session
#
# def get_session() -> dict:
#     """החזרת ה־SESSION של השיחה הנוכחית."""
#     return getattr(g, "yemot_session", {})
#
# def read_param(
#     param: str,
#     voice: str,
#     keys: str = "",
#     max_taps: int = 1,
#     min_taps: int = 1,
#     sulamit: str | None = None,
#     cochavit: bool = True,
#     read_as: str = "No",
# ) -> str | None:
#     """
#     מקביל לפונקציית read ב-PHP מהפורום:
#     אם אין ערך ב-SESSION → מחזירים פקודת read
#     אם יש ערך → מחזירים אותו (הפונקציה אצלך בקוד פשוט לא תקרא return הזה).
#     """
#     session = get_session()
#     if param not in session:
#         # בניית מחרוזת read בסגנון ימות
#         # read=$voice=$param,,$max_taps,$min_taps,,$read_as,,,,$keys
#         resp = f"read={voice}={param},,{max_taps},{min_taps},,{read_as},,,,{keys}"
#         if cochavit and keys:
#             resp += "*"
#         if sulamit:
#             resp += f",,Ok,{sulamit}"
#         return resp
#
#     # יש ערך ב־SESSION – אפשר להשתמש בו בקוד הלוגיקה
#     return None
#
# def unset_session_values(keys: str) -> None:
#     """
#     מקביל ל-unset_session_values ב-PHP:
#     מקבל מחרוזת של מפתחות, מופרדים בפסיק.
#     לדוגמה: "param1,param2,param3:extra"
#     """
#     session = get_session()
#     for raw in keys.split(","):
#         key = raw.split(":", 1)[0].strip()
#         if key:
#             session.pop(key, None)
#
# def reload_module(voice: str | None = None, unset: str | None = None) -> str:
#     """
#     מקביל ל-reload_module ב-PHP:
#     מחיקת ערכים מה-SESSION + חזרה לאותה שלוחה.
#     """
#     if unset:
#         unset_session_values(unset)
#
#     ext = request.args.get("ApiExtension", "")
#
#     parts = []
#     if voice:
#         parts.append(f"id_list_message={voice}")
#     parts.append(f"go_to_folder=/{ext}")
#     return "&".join(parts)
#
# def go_to_folder(folder: str = "/", voice: str | None = None) -> str:
#     """
#     מקביל ל-go_to_folder ב-PHP
#     """
#     parts = []
#     if voice:
#         parts.append(f"id_list_message={voice}")
#     parts.append(f"go_to_folder={folder}")
#     return "&".join(parts)


# ivr/yemot_session.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request

# חנות SESSION בזיכרון (רצוי להחליף לרדיס בפרודקשן)
SESSION_STORE: dict[str, dict[str, str]] = {}

# TTL כדי למנוע זיכרון מתנפח
SESSION_TTL_MIN = 60
SESSION_META: dict[str, datetime] = {}  # call_id -> last_seen (UTC)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _cleanup_expired_sessions() -> None:
    if not SESSION_META:
        return
    cutoff = _utcnow() - timedelta(minutes=SESSION_TTL_MIN)
    expired = [call_id for call_id, ts in SESSION_META.items() if ts < cutoff]
    for call_id in expired:
        SESSION_META.pop(call_id, None)
        SESSION_STORE.pop(call_id, None)


def init_yemot_session(request: Request) -> dict[str, str]:
    """
    FastAPI version:
    - session key is ApiCallId
    - store last query param into session, compatible with your old PHP logic.
    """
    _cleanup_expired_sessions()

    call_id = request.query_params.get("ApiCallId")
    if not call_id:
        request.state.yemot_call_id = None
        request.state.yemot_session = {}
        return request.state.yemot_session

    session = SESSION_STORE.setdefault(call_id, {})
    SESSION_META[call_id] = _utcnow()

    # Save last param from query string (like your legacy behavior)
    qs = str(request.url.query or "")
    if qs:
        last_param = qs.split("&")[-1]
        if "=" in last_param:
            key, value = last_param.split("=", 1)
            session[key] = value

    request.state.yemot_call_id = call_id
    request.state.yemot_session = session
    return session


def get_session(request: Request) -> dict[str, str]:
    return getattr(request.state, "yemot_session", {})


def unset_session_values(request: Request, keys: str) -> None:
    session = get_session(request)
    for raw in keys.split(","):
        key = raw.split(":", 1)[0].strip()
        if key:
            session.pop(key, None)


def reload_module(request: Request, voice: str | None = None, unset: str | None = None) -> str:
    if unset:
        unset_session_values(request, unset)

    ext = request.query_params.get("ApiExtension", "")
    parts: list[str] = []
    if voice:
        parts.append(f"id_list_message={voice}")
    parts.append(f"go_to_folder=/{ext}")
    return "&".join(parts)


def go_to_folder(folder: str = "/", voice: str | None = None) -> str:
    parts: list[str] = []
    if voice:
        parts.append(f"id_list_message={voice}")
    parts.append(f"go_to_folder={folder}")
    return "&".join(parts)
