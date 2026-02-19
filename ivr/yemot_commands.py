from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Union, Literal

from ivr.formatters import clean


# =========================
# Message model (Text / File)
# =========================

@dataclass(frozen=True)
class YemotFile:
    """
    Represents a Yemot audio file reference.
    Examples:
      YemotFile("000")       -> f-000
      YemotFile("/1/000")    -> f-/1/000
    """
    path: str


YemotMessage = Union[str, YemotFile, tuple[Literal["file"], str]]

_YEMOT_PREFIXES = ("f-", "t-", "s-", "date-", "dateH-", "z-", "m-", "n-", "a-", "d-")

AUDIO_ROOT = "/99"

PROMPTS = {
    # System / errors
    "ERR_PHONE_NOT_FOUND": "900",
    "ERR_SYSTEM": "901",
    "ERR_GENERIC": "902",
    "ERR_INVALID_CHOICE": "903",
    "ERR_UNSUPPORTED": "990",

    # Auth / registration
    "AUTH_ENTER_SECRET": "100",
    "AUTH_WRONG_CODE": "904",
    "REG_ENTER_BANK": "110",
    "REG_ENTER_BRANCH": "111",
    "REG_ENTER_ACCOUNT": "112",
    "REG_SUCCESS": "950",

    # Balance / currency
    "BAL_YOUR_BALANCE_IS": "200",
    "CUR_SHEKELS": "201",
    "CUR_AND": "202",
    "CUR_AGOROT": "203",

    # Transfer
    "TR_ENTER_TO_PHONE": "300",
    "TR_ENTER_AMOUNT": "301",
    "TR_AMOUNT_INVALID": "905",
    "TR_USER_NOT_FOUND": "906",
    "TR_SUCCESS": "951",

    # Payment request create
    "PR_ENTER_PHONE": "400",
    "PR_ENTER_AMOUNT": "401",
    "PR_SUCCESS": "952",

    # Deposit / withdraw
    "DEP_ENTER_AMOUNT": "500",
    "DEP_SUCCESS": "953",
    "WDR_ENTER_AMOUNT": "510",
    "WDR_SUCCESS": "954",

    # Received requests
    "RR_FETCH_ERROR": "920",
    "RR_NONE_PENDING": "921",
    "RR_NO_MORE": "922",
    "RR_IDENTIFY_ERROR": "923",
    "RR_DONE": "955",
    "RR_FROM": "610",
    "RR_AMOUNT": "611",
    "RR_MENU": "612",
    "RR_APPROVED_OK": "613",
    "RR_REJECTED_OK": "614",

    # Sent requests
    "SR_FETCH_ERROR": "930",
    "SR_NONE": "931",
    "SR_MORE_OR_BACK": "632",
    "SR_END": "633",

    # History
    "HIST_RANGE_MENU": "700",
    "HIST_ENTER_START": "701",
    "HIST_ENTER_END": "702",
    "HIST_DATE_INVALID": "907",
    "HIST_END_BEFORE_START": "908",
    "HIST_FETCH_ERROR": "940",
    "HIST_EMPTY": "941",
    "HIST_MORE_OR_BACK": "703",
    "HIST_END": "704",

    # Edit profile
    "EDIT_DONE": "960",
    "EDIT_FETCH_USER_ERROR": "942",
    "EDIT_UPDATE_ERROR": "943",
    "EDIT_UPDATED": "961",
    "EDIT_EXIT": "962",
    "EDIT_ENTER_PREFIX": "800",
    "EDIT_ENTER_SUFFIX": "801",
    "EDIT_FIELD_IS": "802",
    "EDIT_CURRENT_VALUE_IS": "803",
    "EDIT_MENU": "804",
}


def prompt_path(key: str) -> str:
    """
    מחזיר נתיב מלא לקובץ הקלטה לפי מפתח.
    לדוגמה: key="ERR_SYSTEM" -> "/99/901"
    """
    file_id = PROMPTS.get(key)
    if not file_id:
        raise KeyError(f"Missing prompt key: {key}")
    return f"{AUDIO_ROOT}/{file_id}"


def yemot_first_part(message: YemotMessage, *, clean_text: bool = True) -> str:
    """
    Builds the first part (id_list_message) for Yemot commands.
    - Plain text -> t-...
    - YemotFile / ("file", "...") -> f-...
    - If already prefixed (f-/t-/...) -> returned as-is
    """
    # tuple shorthand: ("file", "000")
    if isinstance(message, tuple):
        kind, data = message
        if kind != "file":
            raise ValueError(f"Unsupported tuple kind: {kind!r}")
        message = YemotFile(data)

    # YemotFile -> f-...
    if isinstance(message, YemotFile):
        p = (message.path or "").strip()
        if not p:
            raise ValueError("Empty YemotFile path")
        return p if p.startswith("f-") else f"f-{p}"

    # string -> maybe already prefixed; else t-...
    s = str(message)
    if s.startswith(_YEMOT_PREFIXES):
        return s

    s = clean(s) if clean_text else s
    return f"t-{s}"


# =========================
# Core commands
# =========================

def yemot_read(
        text: YemotMessage,
        param: str,
        min_len: int,
        max_len: int,
        timeout: int = 10,
        read_type: str = "Digits",
        confirm: bool = True,
) -> str:
    confirm_value = "yes" if confirm else "no"

    first_part = yemot_first_part(text, clean_text=True)

    # NOTE: leaving your existing second_part format exactly as-is
    second_part = (
        f"{param},,{max_len},{min_len},{timeout},{read_type}"
        f",,,,,,,,,{confirm_value}"
    )

    return f"read={first_part}={second_part}"


def yemot_menu(
        text: Union[YemotMessage, list[YemotMessage]],
        var: str,
        *,
        timeout: int = 7,
        options: str = "1.2.3",
        confirm: bool = False,
) -> str:
    confirm_value = "yes" if confirm else "no"

    if isinstance(text, list):
        first_part = yemot_render_parts(text, clean_text=True)
    else:
        first_part = yemot_first_part(text, clean_text=True)

    return f"read={first_part}={var},Digits,1,1,{timeout},No,AskNo,,,{options},,,,,,,,{confirm_value}"


def yemot_say(message: YemotMessage, *, go_to_folder: str | None = None) -> str:
    """
    Unified 'id_list_message' builder (text or file).
    """
    base = f"id_list_message={yemot_first_part(message, clean_text=True)}"
    return f"{base}&go_to_folder={go_to_folder}" if go_to_folder else base


def yemot_say_parts(parts: list[YemotMessage], *, go_to_folder: str | None = None) -> str:
    """
    Say a sequence of parts (text/files) in order.
    IMPORTANT: Yemot separates id_list_message parts using '.' (dot), not ','.
    """
    joined = ".".join(yemot_first_part(p, clean_text=True) for p in parts)
    base = f"id_list_message={joined}"
    return f"{base}&go_to_folder={go_to_folder}" if go_to_folder else base


def yemot_render_parts(parts: list[YemotMessage], *, clean_text: bool = True) -> str:
    return ".".join(yemot_first_part(p, clean_text=clean_text) for p in parts)


def yemot_play(message: YemotMessage, *, go_to_folder: str | None = None) -> str:
    """
    Unified 'play' builder. Prefers playing files; if text passed, falls back to say.
    """
    first = yemot_first_part(message, clean_text=True)
    if not first.startswith("f-"):
        return yemot_say(message, go_to_folder=go_to_folder)
    base = f"play={first}"
    return f"{base}&go_to_folder={go_to_folder}" if go_to_folder else base


# =========================
# System / Error prompts (audio-first)
# =========================


def yemot_error(
        key: str,
        *,
        go_to_folder: str | None = None,
        hangup: bool = False,
        fallback_text: str = "שגיאה"
) -> str:
    """
    מחזיר הודעת שגיאה מוקלטת לפי key מתוך PROMPTS (בתיקיית /99).
    אם אין מיפוי - נופל לטקסט.
    """
    try:
        path = prompt_path(key)  # "/99/901" וכו'
        resp = yemot_say(YemotFile(path), go_to_folder=go_to_folder)
    except KeyError:
        resp = yemot_say(fallback_text, go_to_folder=go_to_folder)

    if hangup:
        resp = f"{resp}&hangup"

    return resp


def yemot_prompt(key: str) -> YemotFile:
    """
    מחזיר YemotFile עם נתיב מלא לפי PROMPTS.
    שימושי ל-yemot_read / yemot_menu / yemot_say
    """
    return YemotFile(prompt_path(key))


# =========================
# Existing date utilities (unchanged)
# =========================

def parse_ddmmyyyy(s: str) -> datetime | None:
    """
    מקבל מחרוזת 8 ספרות: ddmmyyyy (למשל 08022026)
    ומחזיר datetime ב-UTC בתחילת היום (timezone-aware).
    """
    s = (s or "").strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        dt = datetime.strptime(s, "%d%m%Y")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def get_history_range(choice: str, session: dict, now: datetime) -> tuple[datetime | None, datetime | None]:
    """
    now חייב להיות timezone-aware (UTC)
    """
    if choice == "1":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return start, end

    if choice == "2":
        days_from_sunday = (now.weekday() + 1) % 7
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_from_sunday)
        end = now
        return start, end

    if choice == "3":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
        return start, end

    if choice == "__custom_range__":
        start_iso = session.get("history_range_start_iso")
        end_iso = session.get("history_range_end_iso")
        if not start_iso or not end_iso:
            return None, None
        try:
            start = datetime.fromisoformat(start_iso)
            end = datetime.fromisoformat(end_iso)
            return start, end
        except ValueError:
            return None, None

    return None, None
