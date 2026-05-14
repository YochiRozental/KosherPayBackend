from __future__ import annotations

from fastapi import APIRouter, Depends

from auth.dependencies import require_admin
from db.deps import get_db
from domain.admin_services import get_all_users_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
async def get_all_users(
        conn=Depends(get_db),
        _admin: dict = Depends(require_admin),
):
    return get_all_users_service(conn)
