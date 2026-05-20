from __future__ import annotations

from il_bank_validator import validate_israeli_bank_account

from repositories.bank_repo import (
    get_bank_by_code,
    get_active_bank_branch,
    normalize_bank_code,
    normalize_branch_code,
    normalize_account_number,
)


def validate_bank(conn, *, bank_number: str) -> dict:
    try:
        bank_number = normalize_bank_code(bank_number)
    except ValueError:
        return {
            "valid": False,
            "error_code": "INVALID_BANK_FORMAT",
            "message": "מספר בנק חייב להכיל ספרות בלבד",
        }

    bank = get_bank_by_code(conn, bank_number=bank_number)

    if not bank:
        return {
            "valid": False,
            "error_code": "BANK_NOT_FOUND",
            "message": "בנק זה אינו קיים",
        }

    return {
        "valid": True,
        "bank_code": bank["bank_code"],
        "bank_name": bank["bank_name"],
    }


def validate_bank_branch(conn, *, bank_number: str, branch_number: str) -> dict:
    bank_result = validate_bank(conn, bank_number=bank_number)

    if not bank_result["valid"]:
        return bank_result

    try:
        branch_number = normalize_branch_code(branch_number)
    except ValueError:
        return {
            "valid": False,
            "error_code": "INVALID_BRANCH_FORMAT",
            "message": "מספר סניף חייב להכיל ספרות בלבד",
            "bank_code": bank_result["bank_code"],
            "bank_name": bank_result["bank_name"],
        }

    branch = get_active_bank_branch(
        conn,
        bank_number=bank_result["bank_code"],
        branch_number=branch_number,
    )

    if not branch:
        return {
            "valid": False,
            "error_code": "BRANCH_NOT_FOUND_IN_BANK",
            "message": "סניף זה אינו קיים בבנק זה",
            "bank_code": bank_result["bank_code"],
            "bank_name": bank_result["bank_name"],
        }

    return {
        "valid": True,
        "id": branch["id"],
        "bank_code": branch["bank_code"],
        "bank_name": branch["bank_name"],
        "branch_code": branch["branch_code"],
        "branch_name": branch["branch_name"],
        "city": branch["city"],
        "address": branch["address"],
    }


def validate_bank_account(conn, *, bank_number: str, branch_number: str, account_number: str) -> dict:
    """
    בודקת אם מספר חשבון תקין אלגוריתמית, ותואם לבנק ולסניף (שחייבים להיות קיימים ופעילים).
    """
    # 1. קודם כל בודקים שהבנק והסניף קיימים ופעילים מול ה-DB שלך
    branch_result = validate_bank_branch(conn, bank_number=bank_number, branch_number=branch_number)

    if not branch_result["valid"]:
        return branch_result

    # 2. נורמליזציה של מספר החשבון (וידוא שזה רק מספרים)
    try:
        account_number = normalize_account_number(account_number)
    except ValueError:
        return {
            "valid": False,
            "error_code": "INVALID_ACCOUNT_FORMAT",
            "message": "מספר חשבון חייב להכיל ספרות בלבד",
            "bank_code": branch_result["bank_code"],
            "branch_code": branch_result["branch_code"],
        }

    # 3. בדיקת תקינות אלגוריתמית של החשבון מול הבנק והסניף
    bank_code = branch_result["bank_code"]
    branch_code = branch_result["branch_code"]

    # בדיקת מספר החשבון לפי כללי אימות חשבונות ישראליים
    try:
        is_algorithm_valid = validate_israeli_bank_account(
            bank_code=int(bank_code),
            branch_code=int(branch_code),
            account_number=account_number,
        )
    except (ValueError, TypeError):
        return {
            "valid": False,
            "error_code": "BANK_VALIDATION_FAILED",
            "message": "לא ניתן היה לאמת את מספר החשבון",
            "bank_code": bank_code,
            "branch_code": branch_code,
        }

    if not is_algorithm_valid:
        return {
            "valid": False,
            "error_code": "INVALID_ACCOUNT_ALGORITHM",
            "message": "מספר החשבון אינו תואם לסניף ולבנק",
            "bank_code": bank_code,
            "branch_code": branch_code,
        }

    # תקין מבנית ואלגוריתמית
    return {
        "valid": True,
        "account_number": account_number,
        "bank_code": bank_code,
        "bank_name": branch_result["bank_name"],
        "branch_code": branch_code,
        "branch_name": branch_result["branch_name"],
        "bank_branch_id": branch_result["id"],
    }
