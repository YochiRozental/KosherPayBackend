from fastapi import APIRouter, Depends, HTTPException, status
import psycopg2.extras

from db.deps import get_db
from auth.dependencies import require_admin
from schemas.admin import UsersListResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users", response_model=UsersListResponse)
async def get_all_users(conn=Depends(get_db), _admin: dict = Depends(require_admin)):
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    u.id,
                    u.name,
                    u.id_number,
                    u.role,
                    u.status,
                    up.phone_number,
                    w.current_balance AS balance,
                    w.currency
                FROM users u
                LEFT JOIN user_phones up
                       ON up.user_id = u.id AND up.is_primary = TRUE
                LEFT JOIN wallets w
                       ON w.user_id = u.id
                ORDER BY u.id DESC
                """
            )
            users = cur.fetchall()

        return {"success": True, "users": users}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "שגיאה במערכת", "error": str(e)},
        )
