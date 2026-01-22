# from flask import request
#
# from datetime import datetime, timedelta
# from unused.help import format_date_for_ivr
# from ivr.yemot_helpers import yemot_read
# from ivr.yemot_session import get_session
#
# def handle_amount_action(phone_number, amount_param, read_text, action_func):
#     amount = int(request.args.get(amount_param, 0))
#     if amount == 0:
#         return yemot_read(read_text, amount_param, 1, 7)
#
#     message = action_func(phone_number, amount)['message'].replace('.', ' ')
#     return f"id_list_message=t-{message}&go_to_folder=../"
#
# def format_action_result(result, success_text=None):
#     msg = result.get('message', 'שגיאה כללית').replace('.', ' ')
#     if result.get('success') and success_text:
#         return f"{success_text}&go_to_folder=../"
#     return f"t-{msg}&go_to_folder=../"
#
# def get_pending_requests(result):
#     return [r for r in result['requests'] if r.get("status") == "pending"]
#
# def format_history_line(tr):
#     desc = tr["description"].replace(".", " ").replace("-", " ")
#     dt = tr["transaction_date"]
#     if isinstance(dt, str):
#         dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
#     return f"{format_date_for_ivr(dt + timedelta(hours=2))}: {desc}"
#
# def handle_payment_action(phone_number, action_func, success_text, fail_text, clear_session=False):
#     session = get_session()
#     req_id = session.get("req_id")
#
#     if not req_id:
#         return "id_list_message=t-לא נמצא מספר בקשה.&go_to_folder=../"
#
#     try:
#         result = action_func(phone_number, int(req_id))
#     except ValueError:
#         return "id_list_message=t-מספר בקשה אינו תקין&go_to_folder=../"
#
#     if result.get("success"):
#         if clear_session:
#             session.pop("req_id", None)
#         return f"id_list_message=t-{success_text}&go_to_folder=../"
#
#     return f"id_list_message=t-{fail_text}&go_to_folder=../"


# ivr/yemot_actions.py
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import Request
from unused.help import format_date_for_ivr

from ivr.yemot_helpers import yemot_read
from ivr.yemot_session import get_session


def handle_amount_action(request: Request, phone_number: str, amount_param: str, read_text: str, action_func):
    amount = int(request.query_params.get(amount_param, "0"))
    if amount == 0:
        return yemot_read(read_text, amount_param, 1, 7)

    message = action_func(phone_number, amount)["message"].replace(".", " ")
    return f"id_list_message=t-{message}&go_to_folder=../"


def format_action_result(result: dict, success_text: str | None = None) -> str:
    msg = result.get("message", "שגיאה כללית").replace(".", " ")
    if result.get("success") and success_text:
        return f"{success_text}&go_to_folder=../"
    return f"t-{msg}&go_to_folder=../"


def get_pending_requests(result: dict):
    return [r for r in result["requests"] if r.get("status") == "pending"]


def format_history_line(tr: dict) -> str:
    desc = tr["description"].replace(".", " ").replace("-", " ")
    dt = tr.get("created_at") or tr.get("transaction_date")
    if isinstance(dt, str):
        # התאימי לפורמט המוחזר אצלך אם צריך
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return f"{format_date_for_ivr(dt + timedelta(hours=2))}: {desc}"


def handle_payment_action(
        request: Request,
        phone_number: str,
        action_func,
        success_text: str,
        fail_text: str,
        clear_session: bool = False,
):
    session = get_session(request)
    req_id = session.get("req_id")

    if not req_id:
        return "id_list_message=t-לא נמצא מספר בקשה.&go_to_folder=../"

    try:
        result = action_func(phone_number, int(req_id))
    except ValueError:
        return "id_list_message=t-מספר בקשה אינו תקין&go_to_folder=../"

    if result.get("success"):
        if clear_session:
            session.pop("req_id", None)
        return f"id_list_message=t-{success_text}&go_to_folder=../"

    return f"id_list_message=t-{fail_text}&go_to_folder=../"
