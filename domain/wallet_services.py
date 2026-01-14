from __future__ import annotations
from repositories.wallets_repo import get_wallet_by_user_id

def get_balance(conn, *, user_id: str) -> dict:
    wallet = get_wallet_by_user_id(conn, user_id)

    if not wallet:
        return {"success": False, "message": "לא נמצא ארנק למשתמש"}

    return {
        "success": True,
        "balance": float(wallet["current_balance"]),
        "currency": wallet["currency"],
    }
