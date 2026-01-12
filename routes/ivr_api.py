# from flask import Blueprint, request
# from unused.core import (
#     authenticate_user, open_account, check_balance,
#     deposit_funds, withdraw_funds, transfer_funds, request_payment,
#     approve_payment, reject_payment, check_user_existence,
#     get_sent_payment_requests,get_payment_requests,
#     get_history_by_date_range
# )
# from ivr.yemot_session import init_yemot_session
# from ivr.yemot_helpers import yemot_read
# from unused.core import authenticate_user
#
# legacy_api = Blueprint('legacy_api', __name__)
#
# @legacy_api.before_request
# def setup_yemot_session():
#     init_yemot_session()
#
# @legacy_api.route('/api', methods=['GET'])
# def handle_legacy_api_request():
#
#     action = request.args.get('action')
#     phone_number = request.args.get('ApiPhone', request.args.get('phone_number'))
#     id_number = request.args.get('id_number')
#     secret_code = request.args.get('secret_code')
#
#     bank_number = request.args.get('bank_number')
#     branch_number = request.args.get('branch_number')
#     account_number = request.args.get('account_number')
#
#     name = request.args.get('name')
#     name_record_id = request.args.get('name_record_id')
#
#     if not action:
#         return "API is working no action"

    # --- שלב 1: טיפול בפעולות שלא דורשות אימות מיידי ---

    # if action == 'check_existence':
    #     if not phone_number:
    #         return "tts=שגיאה: מספר טלפון לא זוהה.\nhangup"

        # result = check_user_existence(phone_number)
        #
        # if not result["success"]:
        #     return f"tts={result.get('message', 'שגיאה במערכת')}\nhangup"
        #
        # if result["exists"]:

        # if not id_number:
        #     return yemot_read("אנא הקש מספר זהות", "id_number", 9, 9, read_type="TeudatZehut", confirm=True)
        # if not secret_code:
        #     return yemot_read("אנא הקש את קוד הגישה שלך", "secret_code", 6, 6, read_type="Digits", confirm=True)
        # auth_result = authenticate_user(phone_number, id_number, secret_code)
        # if auth_result["authenticated"]:
        #     return f"go_to_folder=/2"
        # else:
        #     return "אחד או יותר מהנתונים שְהֵקָשְתָ לא נכונים"

        # else:
        #     return "go_to_folder=3"

    # if action == 'open_account':
    #
    #     if not name:
    #         name = f"user_{phone_number}"
    #
    #     if not name_record_id:
    #         return "record=t-אנא הקלט את שמך לאחר הישמע הצליל,name_record_id,10,1"
    #
    #     if not id_number:
    #         return yemot_read("אנא הקש מספר זהות", "id_number", 9, 9)
    #
    #     if not secret_code:
    #         return yemot_read("הקש קוד סודי", "secret_code", 6, 6)
    #
    #     if not bank_number:
    #         return yemot_read("אנא הקש את מספר הבנק", "bank_number", 2, 2)
    #
    #     if not branch_number:
    #         return yemot_read("הקש את מספר הסניף", "branch_number", 3, 3)
    #
    #     if not account_number:
    #         return yemot_read("הקש מספר חשבון", "account_number", 6, 6)
    #
    #     result = open_account(
    #         phone_number,
    #         id_number,
    #         secret_code,
    #         bank_number,
    #         branch_number,
    #         account_number,
    #         name=name,
    #         name_record_id=name_record_id
    #     )
    #
    #     if result['success']:
    #         return f"go_to_folder=/"
    #     else:
    #         return f"tts={result['message']}\nhangup"

    # --- שלב 2: טיפול בכל שאר הפעולות שדורשות אימות ---
    # try:
    #     if action == 'check_balance':
    #
    #         balance = check_balance(phone_number)['balance']
    #         shekels, agorot = divmod(int(round(balance * 100)), 100)
    #
    #         message_text = (
    #             f"יתרתך הנוכחית היא {shekels} שקלים"
    #             + (f" ו {agorot} אגורות" if agorot else "")
    #         )
    #         return f"id_list_message=t-{message_text}&go_to_folder=../"
    #
    #     elif action == 'transfer':
    #         recipient_phone = request.args.get('recipient_phone')
    #         amount_t = request.args.get('amount_t')
    #
    #         if not recipient_phone:
    #             return yemot_read("הקֵש את מספר הטלפון אליו להעביר את הכסף", "recipient_phone", 10, 9)
    #
    #         if recipient_phone and not amount_t:
    #             return yemot_read("הקֵש סכום להעברה", "amount_t", 8, 1)
    #
    #         if recipient_phone and amount_t:
    #             try:
    #                 amount_value = int(amount_t)
    #
    #                 result = transfer_funds(phone_number, recipient_phone, amount_value)
    #
    #                 message_text = result.get('message', 'שגיאה כללית בהעברה')
    #                 message_text = message_text.replace('.', ' ')
    #
    #                 if result.get('success'):
    #                     return format_action_result(
    #                         result,
    #                         f"הַעַבַרַת {amount_value} שְקָלים לְמספָר {recipient_phone} בוצְעָה בהצלחה"
    #                     )
    #                 else:
    #                     return f"id_list_message=t-{message_text}&go_to_folder=../"
    #
    #             except ValueError:
    #                 return "t-שגיאה: סכום לא תקין הוקש&go_to_folder=/11"
    #         else:
    #             return "t-שגיאה בלתי צפויה בלוגיקת ההעברה&hangup"
    #
    #     elif action == 'request_payment':
    #         recipient_phone = request.args.get('recipient_phone')
    #         amount_r = int(request.args.get('amount_r', 0))
    #
    #         if not recipient_phone:
    #             return yemot_read("הקֵש את מספר הטלפון מננו לבקש את הכסף", "recipient_phone", 10, 9)
    #
    #         if recipient_phone and not amount_r:
    #             return yemot_read("הקֵש סכום לבקשה", "amount_r", 8, 1)
    #
    #         if recipient_phone and amount_r:
    #             try:
    #                 amount_value = int(amount_r)
    #
    #                 result = request_payment(phone_number, recipient_phone, amount_r)
    #
    #                 message_text = result.get('message', 'שגיאה כללית בבקשה')
    #                 message_text = message_text.replace('.', ' ')
    #
    #                 if result.get('success'):
    #                     return f"id_list_message=t-בַקַשַת {amount_value} שְקַלים מִמִספר {recipient_phone} הוגְשָה בהצלחה&go_to_folder=../"
    #                 else:
    #                     return f"id_list_message=t-{message_text}&go_to_folder=../"
    #
    #             except ValueError:
    #                 return "id_list_message=t-שגיאה: סכום לא תקין הוקש&go_to_folder=/11"
    #         else:
    #             return "id_list_message=t-שגיאה בלתי צפויה בלוגיקת ההעברה&hangup"
    #
    #     elif action == 'deposit':
    #         return handle_amount_action(
    #             phone_number,
    #             "amount_d",
    #             "הקֵש את הסכום שברצונך להפקיד",
    #             deposit_funds
    #         )
    #
    #     elif action == 'withdraw':
    #         return handle_amount_action(
    #             phone_number,
    #             "amount_w",
    #             "אנא הקֵש את הסכום שברצונך למשוך",
    #             withdraw_funds
    #         )
    #
    #     elif action == 'received_requests':
    #
    #         session = get_session()
    #
    #         if 'choice' in request.args:
    #
    #             choice = request.args.get('choice')
    #             req_id = request.args.get('req_id')
    #             i = int(request.args.get('i', 0))
    #
    #             result = get_payment_requests(phone_number)
    #             if not result['success']:
    #                 return "id_list_message=t-שגיאה בשליפת בקשות&go_to_folder=../"
    #
    #             requests = get_pending_requests(result)
    #
    #             if len(requests) == 0:
    #                 return "id_list_message=t-לא קיימות בקשות תשלום ממתינות&go_to_folder=../"
    #
    #             if not req_id:
    #                 if i < 0 or i >= len(requests):
    #                     return "id_list_message=t-שגיאה: אינדקס לא תקין&go_to_folder=../"
    #                 req_id = requests[i]['id']
    #
    #             if choice == '1':
    #                 session["req_id"] = str(req_id)
    #                 return "go_to_folder=1"
    #
    #             if choice == '2':
    #                 session["req_id"] = str(req_id)
    #                 return "go_to_folder=2"
    #
    #             if choice == '3':
    #                 next_i = i + 1
    #                 if next_i >= len(requests):
    #                     return "id_list_message=t-לא קיימת בקשת תשלום נוספת&go_to_folder=../"
    #                 session["i"] = next_i
    #                 return "go_to_folder=3"
    #
    #             return "go_to_folder=../"
    #
    #         index = session.get("i", int(request.args.get('i', 0)))
    #         session["i"] = index
    #
    #         result = get_payment_requests(phone_number)
    #
    #         if not result['success']:
    #             return f"id_list_message=t-{result['message']}&go_to_folder=../"
    #
    #         requests = get_pending_requests(result)
    #
    #         if len(requests) == 0:
    #             return "id_list_message=t-לא נמצאו בקשות תשלום שהתקבלו&go_to_folder=../"
    #
    #         if index >= len(requests):
    #             return "id_list_message=t-לא קיימת בקשה נוספת&go_to_folder=../"
    #
    #         req = requests[index]
    #
    #         req_id = req['id']
    #         amount = int(req['amount'])
    #         status = req['status']
    #         name = req.get('requester_name', 'שולח לא ידוע') or 'שולח לא ידוע'
    #
    #         status_hebrew = STATUS_HE.get(status, status)
    #
    #         text = f"בקשה מספר {req_id} מאת {name}, סכום {amount} שקלים, סטטוס {status_hebrew}, לאישור הבקשה הקֵש 1, לדחיית הבקשה הקֵש 2 ולבקשה הבאה הקֵש 3"
    #
    #         return f"read=t-{text}=choice,,1,1,5,Number,,,,1.2.3"
    #
    #     elif action == 'sent_requests':
    #         session = get_session()
    #
    #         offset = int(session.get("sent_offset", 0))
    #         next_choice = request.args.get("next_choice")
    #
    #         if next_choice == "1":
    #             session["sent_offset"] = offset + 10
    #             return "go_to_folder=./"
    #
    #         if next_choice == "2":
    #             session.pop("sent_offset", None)
    #             return "go_to_folder=../"
    #
    #         result = get_sent_payment_requests(phone_number)
    #         if not result["success"]:
    #             session.pop("sent_offset", None)
    #             return f"id_list_message=t-{result['message']}&go_to_folder=../"
    #
    #         requests = result["requests"]
    #         if not requests:
    #             session.pop("sent_offset", None)
    #             return "id_list_message=t-לא נמצאו בקשות תשלום שנשלחו&go_to_folder=../"
    #
    #         batch = requests[offset:offset + 10]
    #
    #         if not batch:
    #             session.pop("sent_offset", None)
    #             return "id_list_message=t-סוף בקשות&go_to_folder=../"
    #
    #         lines = []
    #         for idx, req in enumerate(batch, start=offset + 1):
    #             amount = int(req["amount"])
    #             status = STATUS_HE.get(req["status"], req["status"])
    #             name = req.get("recipient_name") or "נמען לא ידוע"
    #
    #             lines.append(
    #                 f"בקשה אל {name}, סכום {amount} שקלים, סטטוס {status}"
    #             )
    #
    #         message_text = ", ".join(lines)
    #
    #         has_more = offset + 10 < len(requests)
    #
    #         if has_more:
    #             return (
    #                 f"read=t-{message_text}, "
    #                 f"לשמיעת עשר בקשות נוספות הקישו 1, "
    #                 f"לחזרה לתפריט הקודם הקישו 2"
    #                 f"=next_choice,Digits,1,1,No,No,No,10,,,,,,,,no"
    #             )
    #
    #         else:
    #             session.pop("sent_offset", None)
    #             return f"id_list_message=t-{message_text}, סוף בקשות&go_to_folder=../"
    #
    #     elif action == "approve_payment":
    #         return handle_payment_action(
    #             phone_number,
    #             approve_payment,
    #             "הבקשה אושרה",
    #             "פעולת האישור נכשלה"
    #         )
    #
    #     elif action == "reject_payment":
    #         return handle_payment_action(
    #             phone_number,
    #             reject_payment,
    #             "הבקשה נדחתה בהצלחה",
    #             "פעולת הדחייה נכשלה",
    #             clear_session=True
    #         )
    #
    #     elif action == 'history':
    #
    #         session = get_session()
    #         session.setdefault("history_offset", 0)
    #         session.setdefault("history_choice", None)
    #
    #         if "history_start" in session and "history_end" in session:
    #             try:
    #                 start = datetime.strptime(session["history_start"], "%d%m%Y")
    #                 end = datetime.strptime(session["history_end"], "%d%m%Y") + timedelta(hours=23, minutes=59, seconds=59)
    #             except ValueError:
    #                 unset_session_values("history_start,history_end")
    #                 return "go_to_folder=./start_date"
    #
    #             session["start"] = start
    #             session["end"] = end
    #             session["history_offset"] = 0
    #
    #             unset_session_values("history_start,history_end")
    #             session["history_choice"] = "__custom_range__"
    #
    #         if "choice" in request.args:
    #             session["history_choice"] = request.args["choice"]
    #
    #         choice = session["history_choice"]
    #
    #         if request.args.get("next_choice") == "2":
    #             unset_session_values("history_offset,history_choice")
    #             return "go_to_folder=./"
    #
    #         current_offset = session["history_offset"] + (10 if request.args.get("next_choice") == "1" else 0)
    #         session["history_offset"] = current_offset
    #
    #         current_offset = session["history_offset"]
    #
    #         if not choice:
    #             text = (
    #                 "עבור פעולות שבוצעו היום הקש 1, "
    #                 "עבור פעולות שבוצעו בשבוע האחרון הקש 2, "
    #                 "עבור פעולות שבוצעו בחודש האחרון הקש 3, "
    #                 "עבור חיפוש לפי טווח תאריכים הקש 4"
    #             )
    #             return f"read=t-{text}=choice,,1,1,5,No,AskNo,,,1.2.3.4"
    #
    #         now = datetime.utcnow() + timedelta(hours=2)
    #
    #         start, end = get_history_range(choice, session, now)
    #         if not start:
    #             return "go_to_folder=./1"
    #
    #         result = get_history_by_date_range(
    #             phone_number=phone_number,
    #             start_date=start,
    #             end_date=end,
    #             offset=current_offset,
    #             limit=11
    #         )
    #
    #         if not result["success"]:
    #             return "id_list_message=t-שגיאה בשליפת היסטוריה&go_to_folder=./"
    #
    #         history = result["history"]
    #
    #         if not history:
    #             unset_session_values("history_offset,history_choice")
    #             return "id_list_message=t-אין פעולות להשמעה&go_to_folder=./"
    #
    #         has_more = len(history) > 10
    #         history = history[:10]
    #
    #         message_text = ", ".join(format_history_line(tr) for tr in history)
    #
    #         if has_more:
    #             return (
    #                 f"read=t-{message_text}, "
    #                 f"לשמיעת עשר פעולות נוספות הקישו 1, לחזרה לתפריט הקודם הקישו 2"
    #                 f"=next_choice,,1,1,5,No,AskNo,,,1.2"
    #             )
    #
    #         else:
    #             unset_session_values("history_offset,history_choice")
    #             return (
    #                 f"id_list_message=t-{message_text} סוף פעולות"
    #                 f"&go_to_folder=./"
    #             )
    #
    #     elif action == "history_start_date":
    #         session = get_session()
    #
    #         if "history_start" in session:
    #             return "go_to_folder=/2/7/2"
    #
    #         return (
    #             "read=t-הקישו תאריך התחלה "
    #             "בפורמט יום חודש שנה"
    #             "=history_start,,8,8,0,Digits"
    #         )
    #
    #     elif action == "history_end_date":
    #         session = get_session()
    #
    #         if "history_end" in session:
    #             return "go_to_folder=/2/7"
    #
    #         start_str = session.get("history_start")
    #
    #         if not start_str:
    #             return "go_to_folder=/2/7/1"
    #
    #         return (
    #             "read=t-הקישו תאריך סיום "
    #             "בפורמט יום חודש שנה"
    #             "=history_end,,8,8,0,Digits"
    #         )
    #
    #
    # except (ValueError, TypeError):
    #     return "שגיאה: הסכום או המזהה שהוזן אינם חוקיים"
    #
    # except Exception as e:
    #     print(f"Legacy API error: {e}")
    #     return "שגיאה במערכת. נסה שוב מאוחר יותר"


# routes/ivr_api.py
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from ivr.yemot_session import init_yemot_session
from ivr.yemot_helpers import yemot_read

# אם את עדיין משתמשת ב-auth הישן ל-IVR:
from unused.core import authenticate_user  # אפשר להחליף בהמשך לדומיין החדש

router = APIRouter(prefix="/ivr", tags=["ivr"])


@router.get("/api", response_class=PlainTextResponse)
async def ivr_entry(request: Request):
    """
    Entry point for Yemot IVR: /ivr/api?action=...
    Returns plain text response (Yemot format).
    """
    init_yemot_session(request)

    action = request.query_params.get("action")
    phone_number = request.query_params.get("ApiPhone") or request.query_params.get("phone_number")
    id_number = request.query_params.get("id_number")
    secret_code = request.query_params.get("secret_code")

    if not action:
        return "API is working no action"

    # פעולה אחת עובדת כמו אצלך כרגע:
    if action == "check_existence":
        if not phone_number:
            return "tts=שגיאה: מספר טלפון לא זוהה.\nhangup"

        if not id_number:
            return yemot_read("אנא הקש מספר זהות", "id_number", 9, 9, read_type="TeudatZehut", confirm=True)
        if not secret_code:
            return yemot_read("אנא הקש את קוד הגישה שלך", "secret_code", 6, 6, read_type="Digits", confirm=True)

        # שימי לב: ב-unused.core.authenticate_user שלך יש חתימה (phone, secret) בלבד בקוד החדש
        # אבל ב-ivr הישן את קוראת עם (phone, id, secret).
        # לכן פה אני קוראת בשיטה שתואמת לקובץ unused.core אצלך (שם זה phone+secret).
        # אם אצלך יש עדיין גרסה עם 3 פרמטרים — תשני בהתאם.
        auth_result = authenticate_user(phone_number, secret_code)

        if auth_result.get("authenticated"):
            return "go_to_folder=/2"
        return "אחד או יותר מהנתונים שהוקשו לא נכונים"

    # ברירת מחדל:
    return "id_list_message=t-פעולה לא נתמכת&go_to_folder=../"
