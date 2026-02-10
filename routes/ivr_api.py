from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from db.deps import get_db
from domain.account_creation_services import open_account
from domain.auth_services import authenticate_user
from domain.payment_requests_services import (
    request_payment,
    get_my_payment_requests,
    approve_payment_request,
    reject_payment_request,
    get_my_sent_payment_requests
)
from domain.transactions_services import (
    transfer, deposit, withdraw, get_transaction_history
)
from domain.users_services import (
    check_user_existence,
    update_me,
    get_me, get_user_id_by_phone_service
)
from domain.wallet_services import get_balance
from ivr.constants import EDIT_FIELDS
from ivr.formatters import present_value, clean, format_sent_request_line, format_text_line
from ivr.yemot_commands import yemot_read, yemot_menu
from ivr.yemot_session import init_yemot_session, session_set, session_get, session_delete

logger = logging.getLogger("kosherpay")
router = APIRouter(prefix="/ivr", tags=["ivr"])


def _get_param(request: Request, key: str) -> str:
    return (request.query_params.get(key) or "").strip()


def require_auth(request):
    user_id = session_get(request, "user_id")
    if not user_id:
        return None, "id_list_message=t-יש להתחבר תחילה&go_to_folder=/"
    return user_id, None


@router.get("/api", response_class=PlainTextResponse)
def ivr_api(request: Request, conn=Depends(get_db)):
    init_yemot_session(request)

    action = _get_param(request, "action")
    phone_number = _get_param(request, "ApiPhone") or _get_param(request, "phone_number")

    if not action:
        return "API is working no action"

    if action == "check_existence":
        if not phone_number:
            return "tts=שגיאה: מספר טלפון לא זוהה.\nhangup"

        result = check_user_existence(conn, phone_number)

        if not result.get("success"):
            msg = (result.get("message") or "שגיאה במערכת").replace("&", " ")
            return f"tts={msg}\nhangup"

        # אם לא קיים → שלוחה 3 (רישום)
        if not result.get("exists"):
            return "go_to_folder=/3"

        # אם קיים → מבקשים קוד סודי
        secret_code = _get_param(request, "secret_code")
        if not secret_code:
            return yemot_read("הקש את הקוד הסודי שלך", "secret_code", 6, 6, read_type="Digits", confirm=True)

        auth = authenticate_user(conn, phone_number, secret_code)

        # ✅ שלב 4: לא לשמור secret_code בסשן
        session_delete(request, "secret_code")

        if not auth.get("success"):
            session_delete(request, "authenticated", "user_id")
            msg = (auth.get("message") or "קוד שגוי").replace("&", " ")
            return f"id_list_message=t-{msg}&go_to_folder=../"

        # ✅ רק אחרי הצלחה — שומרים סשן
        session_set(request, "user_id", auth["user"]["id"])
        session_set(request, "authenticated", "1")
        session_set(request, "phone", phone_number)

        return "go_to_folder=/2"

    if action == "open_account":
        if not phone_number:
            return "tts=שגיאה: מספר טלפון לא זוהה.\nhangup"

        secret_code = _get_param(request, "secret_code")
        bank_number = _get_param(request, "bank_number")
        branch_number = _get_param(request, "branch_number")
        account_number = _get_param(request, "account_number")

        # כרגע שם ברירת מחדל (אפשר להחליף בהקלטה בהמשך)
        name = _get_param(request, "name")
        if not name:
            last4 = phone_number[-4:] if len(phone_number) >= 4 else phone_number
            name = f"user_{last4}"

        if not secret_code:
            return yemot_read("הקש קוד סודי בן 6 ספרות", "secret_code", 6, 6, read_type="Digits", confirm=True)

        if not bank_number:
            return yemot_read("הקש מספר בנק", "bank_number", 2, 2, read_type="Digits", confirm=True)

        if not branch_number:
            return yemot_read("הקש מספר סניף", "branch_number", 3, 3, read_type="Digits", confirm=True)

        if not account_number:
            return yemot_read("הקש מספר חשבון", "account_number", 6, 6, read_type="Digits", confirm=True)

        result = open_account(
            conn,
            phone_number=phone_number,
            secret_code=secret_code,
            name=name,
            bank_number=bank_number,
            branch_number=branch_number,
            account_number=account_number,
        )

        session_delete(request, "secret_code", "bank_number", "branch_number", "account_number", "name")

        if not result.get("success"):
            msg = (result.get("message") or "שגיאה במערכת").replace("&", " ")
            if result.get("error_code") == "PHONE_ALREADY_EXISTS":
                return f"id_list_message=t-{msg}&go_to_folder=/2"
            return f"id_list_message=t-{msg}&go_to_folder=../"

        return "id_list_message=t-נרשמת בהצלחה&go_to_folder=/2"

    if action == "get_balance":
        user_id, err = require_auth(request)
        if err:
            return err

        result = get_balance(conn, user_id=user_id)

        if not result.get("success"):
            msg = (result.get("message") or "שגיאה").replace("&", " ")
            return f"id_list_message=t-{msg}&go_to_folder=../"

        balance = float(result["balance"])
        shekels = int(balance)
        agorot = int(round((balance - shekels) * 100))

        text = f"יתרתך היא {shekels} שקלים"
        if agorot:
            text += f" ו {agorot} אגורות"

        return f"id_list_message=t-{text}&go_to_folder=../"

    if action == "transfer":
        from_user_id, err = require_auth(request)
        if err:
            return err

        to_phone = _get_param(request, "to_phone")
        amount_str = _get_param(request, "amount_transfer")

        if not to_phone:
            return yemot_read(
                "הקש את מספר הטלפון של מקבל ההעברה",
                "to_phone",
                9,
                10,
                read_type="Digits",
                confirm=True,
            )

        if not amount_str:
            return yemot_read(
                "הקש את סכום ההעברה בשקלים ללא אגורות",
                "amount_transfer",
                1,
                8,
                read_type="Number",
                confirm=True,
            )

        # המרה לסכום
        try:
            amount = float(amount_str)
        except ValueError:
            session_delete(request, "amount_transfer")
            return "id_list_message=t-סכום לא תקין&go_to_folder=../"

        to_user_id = get_user_id_by_phone_service(conn, to_phone)
        if not to_user_id:
            session_delete(request, "to_phone", "amount_transfer")
            return "id_list_message=t-לא נמצא משתמש עם המספר שהוקש&go_to_folder=../"

        result = transfer(conn, from_user_id=from_user_id, to_user_id=to_user_id, amount=amount)

        # ניקוי נתוני פעולה (לא להשאיר בזיכרון)
        session_delete(request, "to_phone", "amount_transfer")

        if not result.get("success"):
            msg = (result.get("message") or "שגיאה").replace("&", " ")
            return f"id_list_message=t-{msg}&go_to_folder=../"

        return "id_list_message=t-ההעברה בוצעה בהצלחה&go_to_folder=../"

    if action == "request_payment":
        requester_id, err = require_auth(request)
        if err:
            return err

        pay_req_phone = _get_param(request, "pay_req_phone")
        pay_req_amount_str = _get_param(request, "pay_req_amount")

        if not pay_req_phone:
            return yemot_read(
                "הקש את מספר הטלפון ממי לבקש את התשלום",
                "pay_req_phone",
                9,
                10,
                read_type="Digits",
                confirm=True,
            )

        if not pay_req_amount_str:
            return yemot_read(
                "הקש את סכום הבקשה בשקלים ללא אגורות",
                "pay_req_amount",
                1,
                8,
                read_type="Number",
                confirm=True,
            )

        try:
            amount = float(pay_req_amount_str)
        except ValueError:
            session_delete(request, "pay_req_amount")
            return "id_list_message=t-סכום לא תקין&go_to_folder=../"

        recipient_id = get_user_id_by_phone_service(conn, pay_req_phone)
        if not recipient_id:
            session_delete(request, "pay_req_phone", "pay_req_amount")
            return "id_list_message=t-לא נמצא משתמש עם המספר שהוקש&go_to_folder=../"

        result = request_payment(conn, requester_id=requester_id, recipient_id=recipient_id, amount=amount)

        # ניקוי נתוני פעולה
        session_delete(request, "pay_req_phone", "pay_req_amount")

        if not result.get("success"):
            msg = (result.get("message") or "שגיאה").replace("&", " ")
            return f"id_list_message=t-{msg}&go_to_folder=../"

        req_id = result.get("request_id")
        # לא חובה להשמיע מזהה, אבל אפשר:
        if req_id:
            return f"id_list_message=t-בקשת התשלום נשלחה בהצלחה &go_to_folder=../"

        return "id_list_message=t-בקשת התשלום נשלחה בהצלחה&go_to_folder=../"

    if action == "deposit":
        user_id, err = require_auth(request)
        if err:
            return err

        amount_str = _get_param(request, "amount_d") or _get_param(request, "amount_deposit")

        if not amount_str:
            return yemot_read(
                "הקש את הסכום שברצונך להפקיד בשקלים ללא אגורות",
                "amount_d",
                1,
                8,
                read_type="Number",
                confirm=True,
            )

        try:
            amount = float(amount_str)
        except ValueError:
            session_delete(request, "amount_d", "amount_deposit")
            return "id_list_message=t-סכום לא תקין&go_to_folder=../"

        result = deposit(conn, user_id=user_id, amount=amount)

        # ניקוי נתוני פעולה
        session_delete(request, "amount_d", "amount_deposit")

        if not result.get("success"):
            msg = (result.get("message") or "שגיאה").replace("&", " ")
            return f"id_list_message=t-{msg}&go_to_folder=../"

        return "id_list_message=t-הפקדה בוצעה בהצלחה&go_to_folder=../"

    if action == "withdraw":
        user_id, err = require_auth(request)
        if err:
            return err

        amount_str = _get_param(request, "amount_w") or _get_param(request, "amount_withdraw")

        if not amount_str:
            return yemot_read(
                "הקש את הסכום שברצונך למשוך בשקלים ללא אגורות",
                "amount_w",
                1,
                8,
                read_type="Number",
                confirm=True,
            )

        try:
            amount = float(amount_str)
        except ValueError:
            session_delete(request, "amount_w", "amount_withdraw")
            return "id_list_message=t-סכום לא תקין&go_to_folder=../"

        result = withdraw(conn, user_id=user_id, amount=amount)

        # ניקוי נתוני פעולה
        session_delete(request, "amount_w", "amount_withdraw")

        if not result.get("success"):
            msg = (result.get("message") or "שגיאה").replace("&", " ")
            return f"id_list_message=t-{msg}&go_to_folder=../"

        return "id_list_message=t-משיכה בוצעה בהצלחה&go_to_folder=../"

    if action == "received_requests":
        user_id, err = require_auth(request)
        if err:
            return err

        res = get_my_payment_requests(conn, user_id=user_id)
        if not res.get("success"):
            return "id_list_message=t-שגיאה בשליפת בקשות תשלום&go_to_folder=../"

        requests_list = res.get("requests") or []

        # אם יש לך סטטוס בבקשה (pending/approved/rejected) מומלץ לסנן רק pending:
        pending = [r for r in requests_list if (r.get("status") in (None, "", "pending"))]
        if not pending:
            # ניקוי מצב
            session_delete(request, "req_i", "req_id")
            return "id_list_message=t-לא קיימות בקשות תשלום ממתינות&go_to_folder=../"

        # קריאת state מהסשן
        try:
            i = int(session_get(request, "req_i") or "0")
        except ValueError:
            i = 0

        if i < 0:
            i = 0
        if i >= len(pending):
            # הגענו לסוף
            session_delete(request, "req_i", "req_id")
            return "id_list_message=t-אין בקשות נוספות&go_to_folder=../"

        current = pending[i]
        req_id = str(current.get("id", ""))

        # שמירה בסשן כדי ש-choice ידע על מה לפעול
        session_set(request, "req_i", str(i))
        session_set(request, "req_id", req_id)

        # אם המשתמש כבר בחר 1/2/3
        choice = _get_param(request, "choice")

        # approve
        if choice == "1":
            rid = session_get(request, "req_id")
            if not rid:
                return "id_list_message=t-שגיאה בזיהוי הבקשה&go_to_folder=../"

            out = approve_payment_request(conn, user_id=user_id, request_id=rid)
            # אחרי טיפול — עוברים לבקשה הבאה
            session_set(request, "req_i", str(i + 1))
            session_delete(request, "choice", "req_id")
            msg = (out.get("message") or "בוצע").replace("&", " ")
            # נשארים באותה שלוחה כדי להשמיע את הבקשה הבאה
            return f"id_list_message=t-{msg}&go_to_folder=./"

        # reject
        if choice == "2":
            rid = session_get(request, "req_id")
            if not rid:
                return "id_list_message=t-שגיאה בזיהוי הבקשה&go_to_folder=../"

            out = reject_payment_request(conn, user_id=user_id, request_id=rid)
            session_set(request, "req_i", str(i + 1))
            session_delete(request, "choice", "req_id")
            msg = (out.get("message") or "בוצע").replace("&", " ")
            return f"id_list_message=t-{msg}&go_to_folder=./"

        # next
        if choice == "3":
            session_set(request, "req_i", str(i + 1))
            session_delete(request, "choice", "req_id")
            return "go_to_folder=./"

        # אחרת: צריך להשמיע את הבקשה הנוכחית + להציע 1/2/3
        amount = current.get("amount")
        try:
            amount_num = int(float(amount))
        except (ValueError, TypeError):
            amount_num = 0

        requester_name = current.get("requester_name") or "משתמש"

        text = (
            f"בקשת תשלום מאת {requester_name}. "
            f"סכום {amount_num} שקלים. "
            f"לאישור הקישו 1. לדחייה הקישו 2. לבקשה הבאה הקישו 3."
        )

        resp = yemot_menu(text, "choice", timeout=7, options="1.2.3", confirm=False)
        logger.info("REQ_MENU resp=%s", resp)
        return resp

    if action == "sent_requests":
        user_id, err = require_auth(request)
        if err:
            return err

        page = 5
        sent_next_choice_param = _get_param(request, "sent_next_choice")
        sent_next_choice = sent_next_choice_param or session_get(request, "sent_next_choice")

        if sent_next_choice_param:
            session_set(request, "sent_next_choice", sent_next_choice_param)

        try:
            offset = int(session_get(request, "sent_req_offset") or "0")
        except ValueError:
            offset = 0

        if sent_next_choice == "1":
            offset += page
            session_set(request, "sent_req_offset", str(offset))

        if sent_next_choice == "2":
            session_delete(request, "sent_req_offset", "sent_next_choice")
            return "go_to_folder=../"

        res = get_my_sent_payment_requests(conn, user_id=user_id)
        if not res.get("success"):
            session_delete(request, "sent_req_offset", "sent_next_choice")
            return "id_list_message=t-שגיאה בשליפת בקשות שנשלחו&go_to_folder=../"

        sent = res.get("requests") or []
        if not sent:
            session_delete(request, "sent_req_offset", "sent_next_choice")
            return "id_list_message=t-לא נמצאו בקשות תשלום שנשלחו&go_to_folder=../"

        batch = sent[offset: offset + (page + 1)]
        has_more = len(batch) > page
        batch = batch[:page]

        lines = [format_sent_request_line(dict(r)) for r in batch]
        message_text = " , ".join(lines)

        logger.info("sent_requests message_text: %s", message_text)

        if has_more:
            # כמו שעשית ב-history: בלי אישור על הבחירה
            return (
                f"read=t-{message_text}, "
                f"לשמיעת בקשות נוספות הקישו 1, לחזרה הקישו 2"
                f"=sent_next_choice,Digits,1,1,7,No,No,No,10,,,,,,,,no"
            )

        session_delete(request, "sent_req_offset", "sent_next_choice")
        return f"id_list_message=t-{message_text}, סוף בקשות&go_to_folder=../"

    if action == "history":
        user_id, err = require_auth(request)
        if err:
            return err

        page = 5

        def _reset():
            session_delete(
                request,
                "history_offset",
                "history_next_choice",
                "history_choice",
                "history_start_date",
                "history_end_date",
                "history_range_start_iso",
                "history_range_end_iso",
            )

        # קוראים בחירה/דפדוף גם מה-session
        history_choice = _get_param(request, "history_choice") or session_get(request, "history_choice")
        history_next_choice = _get_param(request, "history_next_choice") or session_get(request, "history_next_choice")

        # חזרה
        if history_next_choice == "2":
            _reset()
            return "go_to_folder=./"

        # offset
        try:
            offset = int(session_get(request, "history_offset") or "0")
        except ValueError:
            offset = 0

        # עוד
        if history_next_choice == "1":
            offset += page
            session_set(request, "history_offset", str(offset))
            session_delete(request, "history_next_choice")

        # אם אין בחירת טווח – תפריט בחירה
        if not history_choice:
            _reset()
            return yemot_menu(
                "לבחירת טווח היסטוריה. להיום הקישו 1. לשבוע הנוכחי הקישו 2. לחודש הנוכחי הקישו 3. לטווח תאריכים הקישו 4.",
                "history_choice",
                timeout=7,
                options="1.2.3.4",
                confirm=False,
            )

        session_set(request, "history_choice", history_choice)

        # טווח מה-session אם קיים
        start_iso = session_get(request, "history_range_start_iso")
        end_iso = session_get(request, "history_range_end_iso")

        if not start_iso or not end_iso:
            # בחירת טווח חדשה -> מאפסים דפדוף
            session_set(request, "history_offset", "0")
            offset = 0

            if history_choice == "4":
                start_str = _get_param(request, "history_start_date") or session_get(request, "history_start_date")
                end_str = _get_param(request, "history_end_date") or session_get(request, "history_end_date")

                if not start_str:
                    return yemot_read("הקש תאריך התחלה בפורמט שמונה ספרות לדוגמה 20260201", "history_start_date", 8, 8,
                                      read_type="Digits", confirm=True)
                if not end_str:
                    return yemot_read("הקש תאריך סיום בפורמט שמונה ספרות לדוגמה 20260208", "history_end_date", 8, 8,
                                      read_type="Digits", confirm=True)

                try:
                    start_dt = datetime.strptime(start_str, "%Y%m%d").replace(hour=0, minute=0, second=0, microsecond=0,
                                                                              tzinfo=timezone.utc)
                    end_dt = datetime.strptime(end_str, "%Y%m%d").replace(hour=23, minute=59, second=59,
                                                                          microsecond=999999, tzinfo=timezone.utc)
                except ValueError:
                    session_delete(request, "history_start_date", "history_end_date")
                    return "id_list_message=t-תאריך לא תקין נסו שוב&go_to_folder=./"

                if end_dt < start_dt:
                    session_delete(request, "history_start_date", "history_end_date")
                    return "id_list_message=t-תאריך סיום לפני תאריך התחלה נסו שוב&go_to_folder=./"
            else:
                now = datetime.now(timezone.utc)
                if history_choice == "1":
                    start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_dt = now
                elif history_choice == "2":
                    days_from_sunday = (now.weekday() + 1) % 7
                    start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_from_sunday)
                    end_dt = now
                elif history_choice == "3":
                    start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_dt = now
                else:
                    session_delete(request, "history_choice")
                    return "id_list_message=t-בחירה לא תקינה&go_to_folder=./"

            session_set(request, "history_range_start_iso", start_dt.isoformat())
            session_set(request, "history_range_end_iso", end_dt.isoformat())
            start_iso = start_dt.isoformat()
            end_iso = end_dt.isoformat()

        # שליפה
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)

        result = get_transaction_history(
            conn,
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            limit=page + 1,
            offset=offset,
        )
        if not result.get("success"):
            session_delete(request, "history_next_choice")
            return "id_list_message=t-שגיאה בשליפת היסטוריה&go_to_folder=./"

        history = result.get("history") or []
        if not history:
            _reset()
            return "id_list_message=t-אין פעולות בטווח שבחרת&go_to_folder=./"

        has_more = len(history) > page
        history = history[:page]

        message_text = clean(" , ".join(format_text_line(dict(tr)) for tr in history))

        if has_more:
            return yemot_menu(
                f"{message_text}. לשמיעת פעולות נוספות הקישו 1. לחזרה הקישו 2.",
                "history_next_choice",
                timeout=7,
                options="1.2",
                confirm=False,
            )

        _reset()
        return f"id_list_message=t-{message_text}, סוף פעולות&go_to_folder=./"

    if action == "edit_profile":
        user_id, err = require_auth(request)
        if err:
            return err

        try:
            idx = int(session_get(request, "edit_idx") or "0")
        except ValueError:
            idx = 0

        # אם הסתיים
        if idx >= len(EDIT_FIELDS):
            session_delete(request, "edit_idx", "edit_choice")
            # מוחקים גם את משתני ה-input אם נשארו
            session_delete(
                request,
                "new_name", "new_phone", "new_secret_code",
                "new_bank_number", "new_branch_number", "new_account_number",
                "new_account_holder"
            )
            return "id_list_message=t-סיימנו לעדכן את הפרטים&go_to_folder=../"

        field_key, label, var_name, mn, mx, read_type = EDIT_FIELDS[idx]

        # להביא משתמש כדי להשמיע ערך נוכחי
        me = get_me(conn, user_id=user_id)  # צריך שיחזיר dict עם שדות תואמים
        if not me or not me.get("success"):
            return "id_list_message=t-שגיאה בשליפת פרטי משתמש&go_to_folder=../"

        user = me.get("user") or {}
        current_value = present_value(field_key, user.get(field_key))

        # אם הגיע קלט חדש לשדה (אחרי yemot_read)
        new_val = _get_param(request, var_name)
        if new_val:
            # מבצעים עדכון
            kwargs = {field_key: new_val}
            out = update_me(conn, user_id=user_id, **kwargs)

            # מנקים את המשתנה כדי שלא “ייתקע”
            session_delete(request, var_name)

            if not out.get("success"):
                msg = clean(out.get("message") or "שגיאה בעדכון")
                # נשארים על אותו שדה כדי שינסה שוב
                return f"id_list_message=t-{msg}&go_to_folder=./"

            # הצליח → עוברים לשדה הבא
            session_set(request, "edit_idx", str(idx + 1))
            return "id_list_message=t-הפרט עודכן&go_to_folder=./"

        # בחירת המשתמש: 1 לערוך, 2 הבא, 3 יציאה
        choice = _get_param(request, "edit_choice")

        if choice == "2":
            session_set(request, "edit_idx", str(idx + 1))
            session_delete(request, "edit_choice")
            return "go_to_folder=./"

        if choice == "3":
            session_delete(request, "edit_idx", "edit_choice")
            session_delete(
                request,
                "new_name", "new_phone", "new_secret_code",
                "new_bank_number", "new_branch_number", "new_account_number",
                "new_account_holder"
            )
            return "id_list_message=t-יציאה מעדכון פרטים&go_to_folder=../"

        if choice == "1":
            session_delete(request, "edit_choice")
            # מבקשים ערך חדש לשדה הנוכחי
            prompt = f"להזנת {label} חדש, הקישו כעת"
            return yemot_read(prompt, var_name, mn, mx, read_type=read_type, confirm=True)

        # אם אין בחירה עדיין: נשמיע שדה + ערך + תפריט
        text = (
            f"הפרט הבא הוא {label}. הערך הנוכחי הוא {current_value}. "
            f"לעדכון הקישו 1. לפרט הבא הקישו 2. ליציאה הקישו 3."
        )
        # תפריט בלי בקשת אישור (confirm=False)
        return yemot_menu(text, "edit_choice", timeout=7, options="1.2.3", confirm=False)

    return "id_list_message=t-פעולה לא נתמכת&go_to_folder=../"
