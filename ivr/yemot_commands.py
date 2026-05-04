from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from typing import Union

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

    "WELCOME_HELLO": "910",

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
    "REG_RECORD_NAME_CHOICE": "911",
    "REG_ENTER_NAME": "912",
    "REG_RECORD_NAME": "913",

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
    "SR_SENT_REQUEST_TO": "620",
    "TODAY": "621",
    "YESTERDAY": "622",
    "DATE": "623",
    "SR_ON_SUM_OF": "624",
    "SR_STATUS_PENDING": "641",
    "SR_STATUS_APPROVED": "642",
    "SR_STATUS_REJECTED": "643",

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
    "HIST_ACT_PAYMENT_REQUEST": "710",  # "בקשת תשלום"
    "HIST_ACT_PAYMENT_APPROVED": "711",  # "אישור בקשת תשלום"
    "HIST_ACT_PAYMENT_REJECTED": "712",  # "דחיית בקשת תשלום"
    "HIST_ACT_TRANSFER": "713",  # "העברה"
    "HIST_ACT_DEPOSIT": "714",  # "הפקדה"
    "HIST_ACT_WITHDRAW": "715",  # "משיכה"
    "HIST_WITH": "705",  # "מול"
    "HIST_PLAYBACK_FROM": "720",  # "השמעת פעולות מ"
    "HIST_PLAYBACK_TO": "721",

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
    "LBL_NAME": "810",
    "LBL_PHONE": "811",
    "LBL_SECRET_CODE": "812",
    "LBL_BANK_NUMBER": "813",
    "LBL_BRANCH_NUMBER": "814",
    "LBL_ACCOUNT_NUMBER": "815",
    "LBL_ACCOUNT_HOLDER": "816",
    "VAL_EMPTY": "899",
}

BACK_VALUE = "BACK"
DEFAULT_IVR_TIMEOUT = 8
MAX_TIMEOUT_REPEATS = 3
TIMEOUT_REPEAT_VALUE = "REPEAT"

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

def is_timeout_repeat(value: str | None) -> bool:
    return value == TIMEOUT_REPEAT_VALUE

def yemot_read(
        text: Union[YemotMessage, list[YemotMessage]],
        param: str,
        min_len: int,
        max_len: int,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        read_type: str = "Digits",
        confirm: bool = True,
        playback: bool = True,
        read_none_ok: bool = False,
        none_value: str = "None",
) -> str:
    confirm_value = "yes" if confirm else "no"
    playback_value = "yes" if playback else "no"

    if isinstance(text, list):
        first_part = yemot_render_parts(text, clean_text=True)
    else:
        first_part = yemot_first_part(text, clean_text=True)

    fields = [""] * 15
    fields[0] = param
    fields[2] = str(max_len)
    fields[3] = str(min_len)
    fields[4] = str(timeout)
    fields[5] = read_type
    fields[6] = playback_value

    if read_none_ok:
        fields[11] = "Ok"
        fields[12] = none_value

    fields[14] = confirm_value

    second_part = ",".join(fields)
    return f"read={first_part}={second_part}"


def read_with_back(
        prompt: YemotMessage | list[YemotMessage],
        param: str,
        min_len: int,
        max_len: int,
        *,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        read_type: str = "Digits",
        confirm: bool = True,
        playback: bool = True,
) -> str:
    return yemot_read(
        prompt,
        param,
        min_len,
        max_len,
        timeout=timeout,
        read_type=read_type,
        confirm=confirm,
        playback=playback,
        read_none_ok=True,
        none_value=TIMEOUT_REPEAT_VALUE,
    )


def yemot_menu(
        text: Union[YemotMessage, list[YemotMessage]],
        var: str,
        *,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        options: str = "1.2.3",
        confirm: bool = False,
        read_none_ok: bool = False,
        none_value: str = "None",
) -> str:
    confirm_value = "yes" if confirm else "no"

    if isinstance(text, list):
        first_part = yemot_render_parts(text, clean_text=True)
    else:
        first_part = yemot_first_part(text, clean_text=True)

    fields = [""] * 15
    fields[0] = var
    fields[1] = "Digits"
    fields[2] = "1"
    fields[3] = "1"
    fields[4] = str(timeout)
    fields[5] = "No"
    fields[6] = "AskNo"
    fields[9] = options

    if read_none_ok:
        fields[11] = "Ok"
        fields[12] = none_value

    fields[14] = confirm_value

    second_part = ",".join(fields)
    return f"read={first_part}={second_part}"


def menu_with_back(
        text: YemotMessage | list[YemotMessage],
        var: str,
        *,
        timeout: int = DEFAULT_IVR_TIMEOUT,
        options: str = "1.2.3",
        confirm: bool = False,
) -> str:
    return yemot_menu(
        text,
        var,
        timeout=timeout,
        options=options,
        confirm=confirm,
        read_none_ok=True,
        none_value=TIMEOUT_REPEAT_VALUE,
    )


def is_back(value: str | None) -> bool:
    return value == BACK_VALUE


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


def yemot_record(
        text: YemotMessage | list[YemotMessage],
        param: str,
        *,
        folder: str,
        file_name: str | None = None,
        finish_on_hash_menu: bool = True,
        save_on_hangup: bool = True,
        append_to_existing: bool = False,
        min_seconds: int | None = None,
        max_seconds: int | None = None,
) -> str:
    if isinstance(text, list):
        first_part = yemot_render_parts(text, clean_text=True)
    else:
        first_part = yemot_first_part(text, clean_text=True)

    fields = [""] * 10
    fields[0] = param
    fields[2] = "record"
    fields[3] = folder
    fields[4] = file_name or ""
    fields[5] = "yes" if finish_on_hash_menu else "no"
    fields[6] = "yes" if save_on_hangup else "no"
    fields[7] = "yes" if append_to_existing else "no"

    if min_seconds is not None:
        fields[8] = str(min_seconds)

    if max_seconds is not None:
        fields[9] = str(max_seconds)

    return f"read={first_part}={','.join(fields)}"


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
