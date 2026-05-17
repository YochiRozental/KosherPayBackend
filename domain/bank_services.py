from __future__ import annotations

from repositories.bank_repo import (
    get_bank_by_code,
    get_active_bank_branch,
    normalize_bank_code,
    normalize_branch_code,
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
        "bank_code": branch["bank_code"],
        "bank_name": branch["bank_name"],
        "branch_code": branch["branch_code"],
        "branch_name": branch["branch_name"],
        "city": branch["city"],
        "address": branch["address"],
    }
