from __future__ import annotations

from datetime import datetime
from typing import Any

from repositories.transactions_repo import (
    create_transaction,
    get_transactions_for_user,
    get_transactions_for_user_in_range,
)


def record_payment_request_decision(
        conn,
        *,
        decision: str,
        amount: float,
        from_user_id: str,
        to_user_id: str,
        request_id: str,
) -> None:
    tx_type = "payment_approve" if decision == "approved" else "payment_reject"
    desc = "אישור בקשת תשלום" if decision == "approved" else "דחיית בקשת תשלום"

    create_transaction(
        conn,
        tx_type=tx_type,
        amount=amount,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        description=desc,
        related_request_id=request_id,
    )


def get_transaction_history(
        conn,
        *,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
) -> dict[str, Any]:
    if start_date is not None and end_date is not None:
        rows = get_transactions_for_user_in_range(
            conn,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
    else:
        rows = get_transactions_for_user(conn, user_id=user_id, limit=limit, offset=offset)

    return {"success": True, "count": len(rows), "history": rows}


def deposit(conn, *, user_id: str, amount: float) -> dict[str, Any]:
    if amount <= 0:
        return {"success": False, "message": "סכום לא תקין"}

    create_transaction(
        conn,
        tx_type="deposit",
        amount=amount,
        from_user_id=None,
        to_user_id=user_id,
        description=f"הפקדה בסך {amount} ₪",
    )
    return {"success": True, "message": "הפקדה בוצעה בהצלחה"}


def withdraw(conn, *, user_id: str, amount: float) -> dict[str, Any]:
    if amount <= 0:
        return {"success": False, "message": "סכום לא תקין"}

    create_transaction(
        conn,
        tx_type="withdraw",
        amount=amount,
        from_user_id=user_id,
        to_user_id=None,
        description=f"משיכה בסך {amount} ₪",
    )
    return {"success": True, "message": "משיכה בוצעה בהצלחה"}


def transfer(conn, *, from_user_id: str, to_user_id: str, amount: float) -> dict[str, Any]:
    if amount <= 0:
        return {"success": False, "message": "סכום לא תקין"}
    if from_user_id == to_user_id:
        return {"success": False, "message": "לא ניתן להעביר לעצמך"}

    create_transaction(
        conn,
        tx_type="transfer",
        amount=amount,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        description=f"העברה בסך {amount} ₪",
    )
    return {"success": True, "message": "ההעברה בוצעה בהצלחה"}
