from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.exc import SQLAlchemyError

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
from domain.recordings_services import get_user_name_recording, save_user_name_recording
from domain.transactions_services import (
    transfer, deposit, withdraw, get_transaction_history
)
from domain.users_services import (
    check_user_existence,
    update_me,
    get_me, get_user_id_by_phone_service
)
from domain.wallet_services import get_balance
from ivr.constants import EDIT_FIELDS, TYPE_HE, IL_TZ, SR_STATUS_KEY_MAP, HIST_TYPE_TO_PROMPT
from ivr.formatters import clean, amount_to_int
from ivr.utils import (
    current_value_msg,
    date_for_yemot,
    get_param,
    get_user_value,
    go_back,
    parse_amount,
    repeatable_read,
    require_auth,
    to_update_kwargs,
)
from ivr.yemot_commands import (
    YemotFile,
    YemotMessage,
    is_back,
    menu_with_back,
    yemot_error,
    yemot_menu,
    yemot_prompt,
    yemot_read,
    yemot_record,
    yemot_say,
    yemot_say_parts,
)
from ivr.yemot_session import init_yemot_session, session_set, session_get, session_delete

logger = logging.getLogger("kosherpay")
router = APIRouter(prefix="/ivr", tags=["ivr"])


@router.get("/api", response_class=PlainTextResponse)
def ivr_api(request: Request, conn=Depends(get_db)):
    init_yemot_session(request)

    action = get_param(request, "action")
    phone_number = get_param(request, "ApiPhone") or get_param(request, "phone_number")

    if not action:
        return "API is working no action"

    if action == "check_existence":
        if not phone_number:
            return yemot_error("ERR_PHONE_NOT_FOUND", hangup=True)

        result = check_user_existence(conn, phone_number)

        if not result.get("success"):
            return yemot_error("ERR_SYSTEM", hangup=True)

        if not result.get("exists"):
            return "go_to_folder=/3"

        secret_code = get_param(request, "secret_code")
        if not secret_code:
            return yemot_read(
                yemot_prompt("AUTH_ENTER_SECRET"),
                "secret_code",
                6, 6,
                read_type="Digits",
                confirm=True
            )

        auth = authenticate_user(conn, phone_number, secret_code)
        session_delete(request, "secret_code")

        if not auth.get("success"):
            session_delete(request, "authenticated", "user_id")
            return yemot_error("AUTH_WRONG_CODE", go_to_folder="/")

        session_set(request, "user_id", auth["user"]["id"])
        session_set(request, "authenticated", "1")
        session_set(request, "phone", phone_number)

        session_set(request, "welcome_played", "0")
        session_set(request, "user_name", auth["user"].get("name", ""))

        return "go_to_folder=/1"

    if action == "welcome":
        user_id, err = require_auth(request)
        if err:
            return err

        if session_get(request, "welcome_played") == "1":
            return "go_to_folder=/2"

        session_set(request, "welcome_played", "1")

        parts: list[YemotMessage] = [
            yemot_prompt("WELCOME_HELLO"),
        ]

        rec = get_user_name_recording(conn, user_id=user_id)

        if rec.get("success") and rec.get("exists") and rec.get("file_path"):
            parts.append(YemotFile(rec["file_path"]))
            return yemot_say_parts(parts, go_to_folder="/2")

        me = get_me(conn, user_id=user_id)

        if me.get("success"):
            name = (me.get("user") or {}).get("name") or ""
            if name:
                parts.append(clean(name))

        return yemot_say_parts(parts, go_to_folder="/2")

    if action == "open_account":
        if not phone_number:
            return yemot_error("ERR_PHONE_NOT_FOUND", hangup=True)

        secret_code = get_param(request, "secret_code") or (session_get(request, "secret_code") or "")
        name_choice = get_param(request, "name_choice") or (session_get(request, "name_choice") or "")
        name = get_param(request, "name") or (session_get(request, "name") or "")
        name_recording = get_param(request, "name_recording") or (session_get(request, "name_recording") or "")
        bank_number = get_param(request, "bank_number") or (session_get(request, "bank_number") or "")
        branch_number = get_param(request, "branch_number") or (session_get(request, "branch_number") or "")
        account_number = get_param(request, "account_number") or (session_get(request, "account_number") or "")
        add_phones_choice = get_param(request, "add_phones_choice") or (session_get(request, "add_phones_choice") or "")
        extra_phone_count = get_param(request, "extra_phone_count") or (session_get(request, "extra_phone_count") or "")
        extra_phone_i = int(session_get(request, "extra_phone_i") or "1")
        extra_phones_raw = session_get(request, "extra_phones") or ""
        extra_phones = [p for p in extra_phones_raw.split(",") if p]

        if not secret_code:
            return yemot_read(
                yemot_prompt("AUTH_ENTER_SECRET"),
                "secret_code",
                6, 6,
                read_type="Digits",
                confirm=True
            )

        if not name_choice:
            return yemot_menu(
                yemot_prompt("REG_RECORD_NAME_CHOICE"),
                "name_choice",
                timeout=8,
                options="1.2",
                confirm=False,
            )

        session_set(request, "name_choice", name_choice)

        if name_choice == "1" and not name_recording:
            file_name = f"name_pending_{phone_number}"
            file_path = f"/99/names/{file_name}"
            session_set(request, "name_recording_path", file_path)

            return yemot_record(
                yemot_prompt("REG_RECORD_NAME"),
                "name_recording",
                folder="/99/names",
                file_name=file_name,
                min_seconds=1,
                max_seconds=10,
            )

        if name_choice == "1" and name_recording:
            session_set(request, "name_recording", name_recording)

        if name_choice == "2" and not name:
            return yemot_read(
                yemot_prompt("REG_ENTER_NAME"),
                "name",
                1, 30,
                read_type="HebrewKeyboard",
                confirm=True,
            )

        if not name:
            last4 = phone_number[-4:] if len(phone_number) >= 4 else phone_number
            name = f"user_{last4}"
            session_set(request, "name", name)

        if not bank_number:
            return yemot_read(
                yemot_prompt("REG_ENTER_BANK"),
                "bank_number",
                2, 2,
                read_type="Number",
                confirm=True
            )

        if not branch_number:
            return yemot_read(
                yemot_prompt("REG_ENTER_BRANCH"),
                "branch_number",
                3, 3,
                read_type="Number",
                confirm=True
            )

        if not account_number:
            return yemot_read(
                yemot_prompt("REG_ENTER_ACCOUNT"),
                "account_number",
                6, 6,
                read_type="Digits",
                confirm=True
            )

        if not add_phones_choice:
            return yemot_menu(
                yemot_prompt("REG_ADD_MORE_PHONES"),
                "add_phones_choice",
                timeout=8,
                options="1.2",
                confirm=False,
            )

        session_set(request, "add_phones_choice", add_phones_choice)

        if add_phones_choice == "1" and not extra_phone_count:
            return yemot_read(
                yemot_prompt("REG_EXTRA_PHONE_COUNT"),
                "extra_phone_count",
                1, 1,
                read_type="Number",
                confirm=True,
            )

        if add_phones_choice == "1":
            session_set(request, "extra_phone_count", extra_phone_count)

            count = int(extra_phone_count or "0")

            if extra_phone_i <= count:
                param_name = f"extra_phone_{extra_phone_i}"
                current_extra_phone = get_param(request, param_name)

                if not current_extra_phone:
                    return yemot_read(
                        yemot_prompt("REG_ENTER_EXTRA_PHONE"),
                        param_name,
                        9, 10,
                        read_type="Digits",
                        confirm=True,
                    )

                current_extra_phone = current_extra_phone.strip()

                # לא לאפשר את המספר הראשי
                if current_extra_phone == phone_number:
                    session_delete(request, param_name)

                    return yemot_say(
                        yemot_prompt("REG_PHONE_ALREADY_EXISTS"),
                        go_to_folder="./",
                    )

                # לא לאפשר כפילות בתוך אותה הרשמה
                if current_extra_phone in extra_phones:
                    session_delete(request, param_name)

                    return yemot_say(
                        yemot_prompt("REG_PHONE_ALREADY_EXISTS"),
                        go_to_folder="./",
                    )

                # לא לאפשר מספר שכבר קיים במערכת
                existing_user = get_user_id_by_phone_service(conn, current_extra_phone)

                if existing_user:
                    session_delete(request, param_name)

                    return yemot_say(
                        yemot_prompt("REG_PHONE_ALREADY_EXISTS"),
                        go_to_folder="./",
                    )

                extra_phones.append(current_extra_phone)

                session_set(request, "extra_phones", ",".join(extra_phones))
                session_set(request, "extra_phone_i", str(extra_phone_i + 1))

                return "go_to_folder=./"


        result = open_account(
            conn,
            phone_number=phone_number,
            secret_code=secret_code,
            name=name,
            bank_number=bank_number,
            branch_number=branch_number,
            account_number=account_number,
            additional_phones=extra_phones,
        )

        if not result.get("success"):
            if result.get("error_code") == "PHONE_ALREADY_EXISTS":
                msg = (result.get("message") or "מספר טלפון כבר רשום").replace("&", " ")
                return yemot_say(msg, go_to_folder="/")

            return yemot_error("ERR_SYSTEM", go_to_folder="../")

        user_id = str(result["user_id"])

        if name_choice == "1":
            file_path = session_get(request, "name_recording_path") or name_recording

            if file_path:
                save_user_name_recording(
                    conn,
                    user_id=user_id,
                    file_path=file_path,
                )

        session_set(request, "user_id", user_id)
        session_set(request, "authenticated", "1")
        session_set(request, "phone", phone_number)

        session_delete(
            request,
            "secret_code",
            "bank_number",
            "branch_number",
            "account_number",
            "name",
            "name_choice",
            "name_recording",
            "name_recording_path",
            "add_phones_choice",
            "extra_phone_count",
            "extra_phone_i",
            "extra_phones",
        )

        return yemot_say(yemot_prompt("REG_SUCCESS"), go_to_folder="/1")

    if action == "get_balance":
        user_id, err = require_auth(request)
        if err:
            return err

        result = get_balance(conn, user_id=user_id)
        if not result.get("success"):
            return yemot_error("ERR_GENERIC", go_to_folder="../")

        balance = float(result["balance"])
        shekels = int(balance)
        agorot = int(round((balance - shekels) * 100))

        if agorot == 100:
            shekels += 1
            agorot = 0

        parts: list[YemotMessage] = [
            yemot_prompt("BAL_YOUR_BALANCE_IS"),
            str(shekels),
            yemot_prompt("CUR_SHEKELS"),
        ]

        if agorot:
            parts += [
                yemot_prompt("CUR_AND"),
                str(agorot),
                yemot_prompt("CUR_AGOROT"),
            ]

        return yemot_say_parts(parts, go_to_folder="../")

    if action == "transfer":
        from_user_id, err = require_auth(request)
        if err:
            return err

        to_phone = get_param(request, "to_phone")
        amount_str = get_param(request, "amount_transfer")

        read_resp = repeatable_read(
            request,
            value=to_phone,
            session_key="transfer_to_phone_timeout_count",
            prompt=yemot_prompt("TR_ENTER_TO_PHONE"),
            param="to_phone",
            min_len=9,
            max_len=10,
            read_type="Digits",
            fail_folder="../",
        )
        if read_resp:
            return read_resp

        if is_back(to_phone):
            return go_back(request, "to_phone", "amount_transfer", target="../")

        to_user_id = get_user_id_by_phone_service(conn, to_phone)
        if not to_user_id:
            session_delete(request, "to_phone", "amount_transfer")
            return yemot_error("TR_USER_NOT_FOUND", go_to_folder="./")

        read_resp = repeatable_read(
            request,
            value=amount_str,
            session_key="transfer_amount_timeout_count",
            prompt=yemot_prompt("TR_ENTER_AMOUNT"),
            param="amount_transfer",
            min_len=1,
            max_len=8,
            read_type="Number",
            fail_folder="./",
        )
        if read_resp:
            return read_resp

        if is_back(amount_str):
            return go_back(request, "to_phone", "amount_transfer", target="./")

        amount = parse_amount(amount_str)
        if amount is None:
            session_delete(request, "amount_transfer")
            return yemot_error("TR_AMOUNT_INVALID", go_to_folder="./")

        result = transfer(conn, from_user_id=from_user_id, to_user_id=to_user_id, amount=amount)

        session_delete(request, "to_phone", "amount_transfer")

        if not result.get("success"):
            return yemot_error("ERR_GENERIC", go_to_folder="../")

        return yemot_say(yemot_prompt("TR_SUCCESS"), go_to_folder="../")

    if action == "request_payment":
        requester_id, err = require_auth(request)
        if err:
            return err

        pay_req_phone = get_param(request, "pay_req_phone")
        pay_req_amount_str = get_param(request, "pay_req_amount")

        read_resp = repeatable_read(
            request,
            value=pay_req_phone,
            session_key="pay_req_phone_timeout_count",
            prompt=yemot_prompt("PR_ENTER_PHONE"),
            param="pay_req_phone",
            min_len=9,
            max_len=10,
            read_type="Digits",
            fail_folder="../",
        )
        if read_resp:
            return read_resp

        if is_back(pay_req_phone):
            return go_back(request, "pay_req_phone", "pay_req_amount", target="../")

        recipient_id = get_user_id_by_phone_service(conn, pay_req_phone)
        if not recipient_id:
            session_delete(request, "pay_req_phone", "pay_req_amount")
            return yemot_error("TR_USER_NOT_FOUND", go_to_folder="./")

        read_resp = repeatable_read(
            request,
            value=pay_req_amount_str,
            session_key="pay_req_amount_timeout_count",
            prompt=yemot_prompt("PR_ENTER_AMOUNT"),
            param="pay_req_amount",
            min_len=1,
            max_len=8,
            read_type="Number",
            fail_folder="./",
        )
        if read_resp:
            return read_resp

        if is_back(pay_req_amount_str):
            return go_back(request, "pay_req_phone", "pay_req_amount", target="./")

        amount = parse_amount(pay_req_amount_str)
        if amount is None:
            session_delete(request, "pay_req_amount")
            return yemot_error("TR_AMOUNT_INVALID", go_to_folder="./")

        result = request_payment(conn, requester_id=requester_id, recipient_id=recipient_id, amount=amount)

        session_delete(request, "pay_req_phone", "pay_req_amount")

        if not result.get("success"):
            return yemot_error("ERR_GENERIC", go_to_folder="../")

        return yemot_say(yemot_prompt("PR_SUCCESS"), go_to_folder="../")

    if action == "deposit":
        user_id, err = require_auth(request)
        if err:
            return err

        amount_str = get_param(request, "amount_d") or get_param(request, "amount_deposit")

        read_resp = repeatable_read(
            request,
            value=amount_str,
            session_key="deposit_amount_timeout_count",
            prompt=yemot_prompt("DEP_ENTER_AMOUNT"),
            param="amount_d",
            min_len=1,
            max_len=8,
            read_type="Number",
            fail_folder="../",
        )
        if read_resp:
            return read_resp

        if is_back(amount_str):
            return go_back(request, "amount_d", "amount_deposit", target="../")

        amount = parse_amount(amount_str)
        if amount is None:
            session_delete(request, "amount_d", "amount_deposit")
            return yemot_error("TR_AMOUNT_INVALID", go_to_folder="./")

        result = deposit(conn, user_id=user_id, amount=amount)

        session_delete(request, "amount_d", "amount_deposit")

        if not result.get("success"):
            return yemot_error("ERR_GENERIC", go_to_folder="../")

        return yemot_say(yemot_prompt("DEP_SUCCESS"), go_to_folder="../")

    if action == "withdraw":
        user_id, err = require_auth(request)
        if err:
            return err

        amount_str = get_param(request, "amount_w") or get_param(request, "amount_withdraw")

        read_resp = repeatable_read(
            request,
            value=amount_str,
            session_key="withdraw_amount_timeout_count",
            prompt=yemot_prompt("WDR_ENTER_AMOUNT"),
            param="amount_w",
            min_len=1,
            max_len=8,
            read_type="Number",
            fail_folder="../",
        )
        if read_resp:
            return read_resp

        if is_back(amount_str):
            return go_back(request, "amount_w", "amount_withdraw", target="../")

        amount = parse_amount(amount_str)
        if amount is None:
            session_delete(request, "amount_w", "amount_withdraw")
            return yemot_error("TR_AMOUNT_INVALID", go_to_folder="./")

        result = withdraw(conn, user_id=user_id, amount=amount)

        session_delete(request, "amount_w", "amount_withdraw")

        if not result.get("success"):
            return yemot_error("ERR_GENERIC", go_to_folder="../")

        return yemot_say(yemot_prompt("WDR_SUCCESS"), go_to_folder="../")

    if action == "received_requests":
        user_id, err = require_auth(request)
        if err:
            return err

        res = get_my_payment_requests(conn, user_id=user_id)
        if not res.get("success"):
            return yemot_error("RR_FETCH_ERROR", go_to_folder="../")

        requests_list = res.get("requests") or []
        pending = [r for r in requests_list if (r.get("status") in (None, "", "pending"))]
        if not pending:
            session_delete(request, "req_i", "req_id")
            return yemot_say(yemot_prompt("RR_NONE_PENDING"), go_to_folder="../")

        try:
            i = int(session_get(request, "req_i") or "0")
        except ValueError:
            i = 0

        if i < 0:
            i = 0
        if i >= len(pending):
            session_delete(request, "req_i", "req_id")
            return yemot_say(yemot_prompt("RR_NO_MORE"), go_to_folder="../")

        current = pending[i]
        req_id = str(current.get("id", ""))

        session_set(request, "req_i", str(i))
        session_set(request, "req_id", req_id)

        choice = get_param(request, "choice")

        last_req = session_get(request, "last_handled_req_id")
        last_choice = session_get(request, "last_handled_choice")

        if choice and last_req == req_id and last_choice == choice:
            session_delete(request, "choice", "req_id")
            return "go_to_folder=./"

        if is_back(choice):
            return go_back(
                request,
                "choice", "req_i", "req_id", "last_handled_req_id", "last_handled_choice",
                target="../",
            )

        if choice == "1":
            approve_payment_request(conn, user_id=user_id, request_id=req_id)

            session_set(request, "last_handled_req_id", req_id)
            session_set(request, "last_handled_choice", "1")
            session_set(request, "req_i", str(i))
            session_delete(request, "choice", "req_id")

            return yemot_say(yemot_prompt("RR_APPROVED_OK"), go_to_folder="./")

        if choice == "2":
            reject_payment_request(conn, user_id=user_id, request_id=req_id)

            session_set(request, "last_handled_req_id", req_id)
            session_set(request, "last_handled_choice", "2")
            session_set(request, "req_i", str(i))
            session_delete(request, "choice", "req_id")

            return yemot_say(yemot_prompt("RR_REJECTED_OK"), go_to_folder="./")

        if choice == "3":
            session_set(request, "req_i", str(i + 1))
            session_delete(request, "choice", "req_id")
            return "go_to_folder=./"

        amount = current.get("amount")

        try:
            amount_num = int(float(amount))
        except (ValueError, TypeError):
            amount_num = 0

        requester_name = current.get("requester_name") or "משתמש"

        parts: list[YemotMessage] = [
            yemot_prompt("RR_FROM"),
            clean(requester_name),
            yemot_prompt("RR_AMOUNT"),
            str(amount_num),
            yemot_prompt("CUR_SHEKELS"),
            yemot_prompt("RR_MENU"),
        ]

        return menu_with_back(
            parts,
            "choice",
            timeout=7,
            options="1.2.3",
            confirm=False,
        )

    if action == "sent_requests":
        user_id, err = require_auth(request)
        if err:
            return err

        page = 5
        sent_next_choice_param = get_param(request, "sent_next_choice")
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

        if is_back(sent_next_choice) or sent_next_choice == "2":
            return go_back(request, "sent_req_offset", "sent_next_choice", target="../")

        res = get_my_sent_payment_requests(conn, user_id=user_id)
        if not res.get("success"):
            session_delete(request, "sent_req_offset", "sent_next_choice")
            return yemot_error("SR_FETCH_ERROR", go_to_folder="../")

        sent = res.get("requests") or []
        if not sent:
            session_delete(request, "sent_req_offset", "sent_next_choice")
            return yemot_say(yemot_prompt("SR_NONE"), go_to_folder="../")

        batch = sent[offset: offset + (page + 1)]
        has_more = len(batch) > page
        batch = batch[:page]

        all_parts: list[YemotMessage] = []

        today_il = datetime.now(IL_TZ).date()
        yesterday_il = today_il - timedelta(days=1)

        for r in batch:
            rr = dict(r)

            recipient_name = rr.get("recipient_name") or rr.get("to_name") or "משתמש"
            amount = rr.get("amount")

            try:
                amount_num = int(float(amount))
            except (ValueError, TypeError):
                amount_num = 0

            status = rr.get("status")
            status_key = SR_STATUS_KEY_MAP.get(status, "SR_STATUS_PENDING")

            created_at_raw = rr.get("created_at") or rr.get("createdAt") or rr.get("requested_at")

            created_dt = None
            if isinstance(created_at_raw, datetime):
                created_dt = created_at_raw
            elif isinstance(created_at_raw, str) and created_at_raw:
                try:
                    created_dt = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                except ValueError:
                    created_dt = None

            if not created_dt:
                date_parts = [yemot_prompt("DATE")]
            else:
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)

                created_date_il = created_dt.astimezone(IL_TZ).date()

                if created_date_il == today_il:
                    date_parts = [yemot_prompt("TODAY")]
                elif created_date_il == yesterday_il:
                    date_parts = [yemot_prompt("YESTERDAY")]
                else:
                    date_str = created_date_il.strftime("%d/%m/%Y")
                    date_parts = [yemot_prompt("DATE"), f"date-{date_str}"]

            all_parts += [
                *date_parts,
                yemot_prompt("SR_SENT_REQUEST_TO"),
                clean(recipient_name),
                yemot_prompt("SR_ON_SUM_OF"),
                str(amount_num),
                yemot_prompt("CUR_SHEKELS"),
                yemot_prompt(status_key),
            ]

        if has_more:
            return menu_with_back(
                all_parts + [yemot_prompt("SR_MORE_OR_BACK")],
                "sent_next_choice",
                timeout=7,
                options="1.2",
                confirm=False,
            )

        session_delete(request, "sent_req_offset", "sent_next_choice")
        return yemot_say_parts(all_parts + [yemot_prompt("SR_END")], go_to_folder="../")

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

        history_choice = get_param(request, "history_choice") or session_get(request, "history_choice")
        history_next_choice = get_param(request, "history_next_choice") or session_get(request,
                                                                                       "history_next_choice")

        if history_next_choice == "2":
            _reset()
            return "go_to_folder=./"

        try:
            offset = int(session_get(request, "history_offset") or "0")
        except ValueError:
            offset = 0

        if history_next_choice == "1":
            offset += page
            session_set(request, "history_offset", str(offset))
            session_delete(request, "history_next_choice")

        if not history_choice:
            _reset()
            return yemot_menu(
                yemot_prompt("HIST_RANGE_MENU"),
                "history_choice",
                timeout=7,
                options="1.2.3.4",
                confirm=False,
            )

        session_set(request, "history_choice", history_choice)

        start_iso = session_get(request, "history_range_start_iso")
        end_iso = session_get(request, "history_range_end_iso")

        if not start_iso or not end_iso:
            session_set(request, "history_offset", "0")
            offset = 0

            if history_choice == "4":
                start_str = get_param(request, "history_start_date") or session_get(request, "history_start_date")
                end_str = get_param(request, "history_end_date") or session_get(request, "history_end_date")

                if not start_str:
                    resp = yemot_read(
                        yemot_prompt("HIST_ENTER_START"),
                        "history_start_date",
                        8, 8,
                        read_type="NO",
                        confirm=False,
                        playback=False,
                    )
                    logger.info("HISTORY start_date read response: %s", resp)
                    return resp

                if not end_str:
                    resp = yemot_read(
                        yemot_prompt("HIST_ENTER_END"),
                        "history_end_date",
                        8, 8,
                        read_type="NO",
                        confirm=False,
                        playback=False,
                    )
                    logger.info("HISTORY end_date read response: %s", resp)
                    return resp

                try:
                    start_dt = datetime.strptime(start_str, "%d%m%Y").replace(
                        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                    )
                    end_dt = datetime.strptime(end_str, "%d%m%Y").replace(
                        hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
                    )
                except ValueError:
                    session_delete(request, "history_start_date", "history_end_date")
                    return yemot_say(yemot_prompt("HIST_DATE_INVALID"), go_to_folder="./")

                if end_dt < start_dt:
                    session_delete(request, "history_start_date", "history_end_date")
                    return yemot_say(yemot_prompt("HIST_END_BEFORE_START"), go_to_folder="./")

            else:
                now = datetime.now(timezone.utc)
                if history_choice == "1":
                    start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_dt = now
                elif history_choice == "2":
                    days_from_sunday = (now.weekday() + 1) % 7
                    start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                        days=days_from_sunday)
                    end_dt = now
                elif history_choice == "3":
                    start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_dt = now
                else:
                    session_delete(request, "history_choice")
                    return yemot_error("ERR_INVALID_CHOICE", go_to_folder="./")

            session_set(request, "history_range_start_iso", start_dt.isoformat())
            session_set(request, "history_range_end_iso", end_dt.isoformat())
            start_iso = start_dt.isoformat()
            end_iso = end_dt.isoformat()

        try:
            start_dt = datetime.fromisoformat(start_iso)
            end_dt = datetime.fromisoformat(end_iso)

        except (TypeError, ValueError):
            _reset()
            return yemot_say(yemot_prompt("HIST_DATE_INVALID"), go_to_folder="./")

        try:
            result = get_transaction_history(
                conn,
                user_id=user_id,
                start_date=start_dt,
                end_date=end_dt,
                limit=page + 1,
                offset=offset,
            )

        except SQLAlchemyError:
            logger.exception("get_transaction_history failed")
            session_delete(request, "history_next_choice")
            return yemot_error("HIST_FETCH_ERROR", go_to_folder="./")

        if not result.get("success"):
            session_delete(request, "history_next_choice")
            return yemot_error("HIST_FETCH_ERROR", go_to_folder="./")

        history = result.get("history") or []
        if not history:
            _reset()
            return yemot_say(yemot_prompt("HIST_EMPTY"), go_to_folder="./")

        has_more = len(history) > page
        history = history[:page]

        all_parts: list[YemotMessage] = []

        if offset == 0:
            all_parts += [
                yemot_prompt("HIST_PLAYBACK_FROM"),
                date_for_yemot(start_dt),
                yemot_prompt("HIST_PLAYBACK_TO"),
                date_for_yemot(end_dt),
            ]

        today_il = datetime.now(IL_TZ).date()
        yesterday_il = today_il - timedelta(days=1)

        for tr in history:
            rr = dict(tr)

            # --- תאריך: היום / אתמול / בתאריך + תאריך ---
            created_at_raw = rr.get("created_at")
            created_dt = created_at_raw if isinstance(created_at_raw, datetime) else None

            if created_dt:
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)

                created_date_il = created_dt.astimezone(IL_TZ).date()

                if created_date_il == today_il:
                    date_parts = [yemot_prompt("TODAY")]
                elif created_date_il == yesterday_il:
                    date_parts = [yemot_prompt("YESTERDAY")]
                else:
                    date_str = created_date_il.strftime("%d/%m/%Y")
                    date_parts = [yemot_prompt("DATE"), f"date-{date_str}"]
            else:
                date_parts = [yemot_prompt("DATE")]

            # --- פעולה ---
            t = rr.get("type")
            action_key = HIST_TYPE_TO_PROMPT.get(t)

            if action_key:
                action_part: YemotMessage = yemot_prompt(action_key)
            else:
                action_text = TYPE_HE.get(t, "פעולה")
                action_part = clean(action_text)

            # --- סכום ---
            amt = amount_to_int(rr.get("amount"))
            amt_parts: list[YemotMessage] = []
            if amt is not None:
                amt_parts = [
                    yemot_prompt("SR_ON_SUM_OF"),
                    str(amt),
                    yemot_prompt("CUR_SHEKELS"),
                ]

            # --- מול (צד שני) ---
            counterparty = rr.get("counterparty") or rr.get("to_name") or rr.get("from_name")
            cp_parts: list[YemotMessage] = []
            if counterparty:
                cp_parts = [yemot_prompt("HIST_WITH"), clean(counterparty)]

            all_parts += [
                *date_parts,
                action_part,
                *amt_parts,
                *cp_parts,
            ]

        if has_more:
            return yemot_menu(
                all_parts + [yemot_prompt("HIST_MORE_OR_BACK")],
                "history_next_choice",
                timeout=7,
                options="1.2",
                confirm=False,
            )

        _reset()
        return yemot_say_parts(all_parts + [yemot_prompt("HIST_END")], go_to_folder="./")

    if action == "edit_profile":
        user_id, err = require_auth(request)
        if err:
            return err

        try:
            idx = int(session_get(request, "edit_idx") or "0")
        except ValueError:
            idx = 0

        if idx >= len(EDIT_FIELDS):
            session_delete(request, "edit_idx", "edit_choice")
            session_delete(
                request,
                "new_name", "new_phone", "new_secret_code",
                "new_bank_number", "new_branch_number", "new_account_number",
                "new_account_holder"
            )
            return yemot_say(yemot_prompt("EDIT_DONE"), go_to_folder="../")

        field_key, label_key, var_name, mn, mx, read_type = EDIT_FIELDS[idx]
        label = yemot_prompt(label_key)

        me = get_me(conn, user_id=user_id)
        if not me or not me.get("success"):
            return yemot_say(yemot_prompt("EDIT_FETCH_USER_ERROR"), go_to_folder="../")

        user = me.get("user") or {}
        raw_val = get_user_value(user, field_key)

        new_val = get_param(request, var_name)
        if new_val:
            kwargs = to_update_kwargs(field_key, new_val, user)
            out = update_me(conn, user_id=user_id, **kwargs)

            session_delete(request, var_name)

            if not out.get("success"):
                return yemot_say(yemot_prompt("EDIT_UPDATE_ERROR"), go_to_folder="./")

            session_set(request, "edit_idx", str(idx + 1))
            return yemot_say(yemot_prompt("EDIT_UPDATED"), go_to_folder="./")

        choice = get_param(request, "edit_choice")

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
            return yemot_say(yemot_prompt("EDIT_EXIT"), go_to_folder="../")

        if choice == "1":
            session_delete(request, "edit_choice")
            return yemot_read(
                [yemot_prompt("EDIT_ENTER_PREFIX"), label, yemot_prompt("EDIT_ENTER_SUFFIX")],
                var_name, mn, mx, read_type=read_type, confirm=True
            )

        parts = [
            yemot_prompt("EDIT_FIELD_IS"),
            label,
            yemot_prompt("EDIT_CURRENT_VALUE_IS"),
            current_value_msg(field_key, raw_val),
            yemot_prompt("EDIT_MENU"),
        ]
        return yemot_menu(parts, "edit_choice", timeout=7, options="1.2.3", confirm=False)

    return "id_list_message=t-פעולה לא נתמכת&go_to_folder=../"
