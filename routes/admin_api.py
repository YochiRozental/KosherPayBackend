from __future__ import annotations

from fastapi import APIRouter, Depends

from auth.dependencies import require_admin
from db.deps import get_db
from domain.admin_services import (
    approve_user_service,
    block_user_service,
    get_all_users_service,
    reject_user_service,
    unblock_user_service,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
async def get_all_users(
        conn=Depends(get_db),
        _admin: dict = Depends(require_admin),
):
    return get_all_users_service(conn)


@router.patch("/users/{user_id}/approve")
async def approve_user(
        user_id: str,
        conn=Depends(get_db),
        _admin: dict = Depends(require_admin),
):
    return approve_user_service(
        conn,
        user_id=user_id,
    )


@router.patch("/users/{user_id}/reject")
async def reject_user(
        user_id: str,
        conn=Depends(get_db),
        _admin: dict = Depends(require_admin),
):
    return reject_user_service(
        conn,
        user_id=user_id,
    )


@router.patch("/users/{user_id}/block")
async def block_user(
        user_id: str,
        conn=Depends(get_db),
        _admin: dict = Depends(require_admin),
):
    return block_user_service(
        conn,
        user_id=user_id,
    )


@router.patch("/users/{user_id}/unblock")
async def unblock_user_route(
        user_id: str,
        conn=Depends(get_db),
        _admin: dict = Depends(require_admin),
):
    return unblock_user_service(
        conn,
        user_id=user_id,
    )
