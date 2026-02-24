from datetime import datetime

from fastapi import HTTPException, status
from fastapi import Request

from ivr.constants import IL_TZ, BANK_MAP
from ivr.yemot_commands import YemotMessage, yemot_prompt
from ivr.yemot_session import session_get


def ensure_success(result: dict, *, status_code: int = status.HTTP_400_BAD_REQUEST) -> dict:
    if not result.get("success"):
        raise HTTPException(status_code=status_code, detail=result)
    return result


def get_user_value(user: dict, field_key: str):
    # שדות בנק מקוננים
    if field_key in BANK_MAP:
        root, inner = BANK_MAP[field_key]
        return (user.get(root) or {}).get(inner)

    # שדות רגילים ברמה העליונה
    return user.get(field_key)


def get_param(request: Request, key: str) -> str:
    return (request.query_params.get(key) or "").strip()


def require_auth(request):
    user_id = session_get(request, "user_id")
    if not user_id:
        return None, "id_list_message=t-יש להתחבר תחילה&go_to_folder=/"
    return user_id, None


def date_for_yemot(dt: datetime) -> str:
    # משמיע תאריך בפורמט שימות יודע: date-dd/mm/yyyy
    d = dt.astimezone(IL_TZ).date()
    return f"date-{d.strftime('%d/%m/%Y')}"


def current_value_msg(field_key: str, v: str) -> YemotMessage:
    v = (v or "").strip()
    if not v:
        return yemot_prompt("VAL_EMPTY")

    # שדות מספריים – נרצה ספרות/מספר
    if field_key in {"phone", "account_number", "secret_code", "bank_number", "branch_number"}:
        digits_only = "".join(ch for ch in v if ch.isdigit())
        if not digits_only:
            return yemot_prompt("VAL_EMPTY")

        # טלפון / קוד סודי / מספר חשבון -> ספרה ספרה
        if field_key in {"phone", "account_number", "secret_code"}:
            return f"d-{digits_only}"

        # מספר בנק / סניף -> מספר שלם
        if field_key in {"bank_number", "branch_number"}:
            return f"n-{digits_only}"

    # שדות טקסט (שם, שם בעל החשבון וכו') -> להשמיע כטקסט
    return v


def to_update_kwargs(field_key: str, new_val: str, user: dict) -> dict:
    new_val = (new_val or "").strip()

    if field_key in {"bank_number", "branch_number", "account_number", "account_holder"}:
        bank = user.get("bankAccount") or {}

        merged = {
            "bank_number": str(bank.get("bankNumber") or "").strip(),
            "branch_number": str(bank.get("branchNumber") or "").strip(),
            "account_number": str(bank.get("accountNumber") or "").strip(),
            "account_holder": str(bank.get("accountHolder") or "").strip(),
        }

        return {**merged, field_key: new_val}

    return {field_key: new_val}
