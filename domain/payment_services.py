# domain/payment_services.py
from __future__ import annotations
from repositories.transactions_repo import create_transaction, get_transactions_for_user

def get_transaction_history(conn, *, user_id: str, limit: int = 20, offset: int = 0) -> dict:
    rows = get_transactions_for_user(conn, user_id=user_id, limit=limit, offset=offset)
    return {"success": True, "count": len(rows), "history": rows}


def deposit(conn, *, user_id: str, amount: float) -> dict:
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


def withdraw(conn, *, user_id: str, amount: float) -> dict:
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


def transfer(conn, *, from_user_id: str, to_user_id: str, amount: float) -> dict:
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
