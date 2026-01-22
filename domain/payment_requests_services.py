from __future__ import annotations

from repositories.payment_requests_repo import approve_pending_request_atomic
from repositories.payment_requests_repo import (
    create_payment_request,
    get_requests_for_user,
    get_sent_requests_for_user,
    reject_pending_request_atomic,
)
from repositories.transactions_repo import create_transaction


def request_payment(conn, *, requester_id: str, recipient_id: str, amount: float) -> dict:
    if amount <= 0:
        return {"success": False, "message": "סכום לא תקין"}
    if requester_id == recipient_id:
        return {"success": False, "message": "לא ניתן לבקש מעצמך"}

    req = create_payment_request(
        conn,
        requester_id=requester_id,
        recipient_id=recipient_id,
        amount=amount,
    )

    return {
        "success": True,
        "message": "בקשת התשלום נשלחה",
        "request_id": str(req["id"]),
    }


def get_my_payment_requests(conn, *, user_id: str) -> dict:
    return {
        "success": True,
        "requests": get_requests_for_user(conn, user_id=user_id),
    }


def get_my_sent_payment_requests(conn, *, user_id: str) -> dict:
    return {
        "success": True,
        "requests": get_sent_requests_for_user(conn, user_id=user_id),
    }


# def approve_payment_request(conn, *, user_id: str, request_id: str) -> dict:
#     row = approve_pending_request_atomic(conn, request_id=request_id, recipient_id=user_id)
#     if not row:
#         return {"success": False, "message": "בקשה לא נמצאה או שכבר טופלה"}
#
#     create_transaction(
#         conn,
#         tx_type="payment_approve",
#         amount=float(row["amount"]),
#         from_user_id=user_id,
#         to_user_id=str(row["requester_id"]),
#         description="אישור בקשת תשלום",
#     )
#     return {"success": True, "message": "הבקשה אושרה"}
#
#
# def reject_payment_request(conn, *, user_id: str, request_id: str) -> dict:
#     ok = reject_pending_request_atomic(conn, request_id=request_id, recipient_id=user_id)
#     if not ok:
#         return {"success": False, "message": "בקשה לא נמצאה או שכבר טופלה"}
#     return {"success": True, "message": "הבקשה נדחתה"}

def approve_payment_request(conn, *, user_id: str, request_id: str) -> dict:
    row = approve_pending_request_atomic(conn, request_id=request_id, recipient_id=user_id)
    if not row:
        return {"success": False, "message": "בקשה לא נמצאה או שכבר טופלה"}

    create_transaction(
        conn,
        tx_type="payment_approve",
        amount=float(row["amount"]),
        from_user_id=str(row["recipient_id"]),  # הכסף יורד מהמקבל (מי שמאשר)
        to_user_id=str(row["requester_id"]),  # ועובר למבקש
        description="אישור בקשת תשלום",
        related_request_id=str(row["id"]),  # ✅ קישור לבקשה
    )

    return {"success": True, "message": "הבקשה אושרה"}


def reject_payment_request(conn, *, user_id: str, request_id: str) -> dict:
    row = reject_pending_request_atomic(conn, request_id=request_id, recipient_id=user_id)
    if not row:
        return {"success": False, "message": "בקשה לא נמצאה או שכבר טופלה"}

    create_transaction(
        conn,
        tx_type="payment_reject",
        amount=float(row["amount"]),
        from_user_id=str(row["recipient_id"]),
        to_user_id=str(row["requester_id"]),
        description="דחיית בקשת תשלום",
        related_request_id=str(row["id"]),
    )

    return {"success": True, "message": "הבקשה נדחתה"}
