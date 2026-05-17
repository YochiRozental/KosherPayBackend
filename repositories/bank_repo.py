from __future__ import annotations


def normalize_bank_code(value: str) -> str:
    value = (value or "").strip()
    if not value.isdigit():
        raise ValueError("bank_number must contain digits only")
    return str(int(value))


def normalize_branch_code(value: str) -> str:
    value = (value or "").strip()
    if not value.isdigit():
        raise ValueError("branch_number must contain digits only")
    return str(int(value))


def normalize_account_number(value: str) -> str:
    value = (value or "").strip()

    if not value.isdigit():
        raise ValueError("account_number must contain digits only")

    return value


def get_bank_by_code(conn, *, bank_number: str) -> dict | None:
    bank_code = normalize_bank_code(bank_number)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT bank_code, bank_name
            FROM bank_branches
            WHERE bank_code = %s
            LIMIT 1
            """,
            (bank_code,),
        )
        return cur.fetchone()


def get_active_bank_branch(conn, *, bank_number: str, branch_number: str) -> dict | None:
    bank_code = normalize_bank_code(bank_number)
    branch_code = normalize_branch_code(branch_number)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, bank_code, branch_code, bank_name, branch_name, city, address
            FROM bank_branches
            WHERE bank_code = %s
              AND branch_code = %s
              AND is_closed = FALSE
            LIMIT 1
            """,
            (bank_code, branch_code),
        )
        return cur.fetchone()
