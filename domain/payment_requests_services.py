# domain/payment_request_services.py
from __future__ import annotations

from repositories.payment_requests_repo import (
    create_payment_request,
    get_pending_requests_for_user,
    approve_pending_request_atomic,
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
    return {"success": True, "message": "בקשת התשלום נשלחה", "request_id": req["id"]}


def get_my_payment_requests(conn, *, user_id: str) -> dict:
    return {"success": True, "requests": get_pending_requests_for_user(conn, user_id=user_id)}


def approve_payment_request(conn, *, user_id: str, request_id: int) -> dict:
    row = approve_pending_request_atomic(conn, request_id=request_id, recipient_id=user_id)
    if not row:
        return {"success": False, "message": "בקשה לא נמצאה או שכבר טופלה"}

    # יצירת העברת כסף - ה-Trigger מטפל בארנקים
    create_transaction(
        conn,
        tx_type="payment_request",
        amount=float(row["amount"]),
        from_user_id=user_id,              # המשלם
        to_user_id=str(row["requester_id"]),  # מקבל הכסף (מבקש)
        description="אישור בקשת תשלום",
    )
    return {"success": True, "message": "הבקשה אושרה"}


def reject_payment_request(conn, *, user_id: str, request_id: int) -> dict:
    ok = reject_pending_request_atomic(conn, request_id=request_id, recipient_id=user_id)
    if not ok:
        return {"success": False, "message": "בקשה לא נמצאה או שכבר טופלה"}
    return {"success": True, "message": "הבקשה נדחתה"}
