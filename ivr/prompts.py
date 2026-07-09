from ivr.commands import yemot_say
from ivr.config import AUDIO_ROOT
from ivr.types import YemotFile

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
    "REG_ADD_MORE_PHONES": "914",
    "REG_EXTRA_PHONE_COUNT": "915",
    "REG_ENTER_EXTRA_PHONE": "916",
    "REG_PHONE_ALREADY_EXISTS": "917",
    "REG_INVALID_BANK": "918",
    "REG_INVALID_BANK_BRANCH": "919",

    "AUTH_ENTER_SECRET_WITH_RESET": "969",
    "FORGOT_SECRET_ENTER_VERIFY_CODE": "970",
    "FORGOT_SECRET_ENTER_NEW_SECRET": "971",
    "FORGOT_SECRET_CALL_FAILED": "972",
    "FORGOT_SECRET_START_FAILED": "973",
    "FORGOT_SECRET_EXPIRED": "974",
    "FORGOT_SECRET_WRONG_CODE": "975",
    "FORGOT_SECRET_RESET_FAILED": "976",
    "FORGOT_SECRET_RESET_SUCCESS_LOGIN": "977",

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

SR_STATUS_KEY_MAP = {
    None: "SR_STATUS_PENDING",
    "": "SR_STATUS_PENDING",
    "pending": "SR_STATUS_PENDING",
    "approved": "SR_STATUS_APPROVED",
    "rejected": "SR_STATUS_REJECTED",
}

HIST_TYPE_TO_PROMPT = {
    "payment_request": "HIST_ACT_PAYMENT_REQUEST",
    "payment_request_approved": "HIST_ACT_PAYMENT_APPROVED",
    "payment_request_rejected": "HIST_ACT_PAYMENT_REJECTED",
    "transfer": "HIST_ACT_TRANSFER",
    "deposit": "HIST_ACT_DEPOSIT",
    "withdraw": "HIST_ACT_WITHDRAW",
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


def yemot_prompt(key: str) -> YemotFile:
    """
    מחזיר YemotFile עם נתיב מלא לפי PROMPTS.
    שימושי ל-yemot_read / yemot_menu / yemot_say
    """
    return YemotFile(prompt_path(key))


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
        path = prompt_path(key)
        resp = yemot_say(YemotFile(path), go_to_folder=go_to_folder)
    except KeyError:
        resp = yemot_say(fallback_text, go_to_folder=go_to_folder)

    if hangup:
        resp = f"{resp}&hangup"

    return resp
