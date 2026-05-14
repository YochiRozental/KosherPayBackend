from __future__ import annotations

from typing import Any

from repositories.bank_branches_repo import (
    get_active_bank_branch,
    get_bank_by_code,
)


def get_bank(conn, *, bank_number: str) -> dict[str, Any] | None:
    return get_bank_by_code(
        conn,
        bank_number=bank_number,
    )


def get_bank_branch(
        conn,
        *,
        bank_number: str,
        branch_number: str,
) -> dict[str, Any] | None:
    return get_active_bank_branch(
        conn,
        bank_number=bank_number,
        branch_number=branch_number,
    )
