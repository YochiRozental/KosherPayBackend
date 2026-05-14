from fastapi import APIRouter

from db.connection import get_db_connection

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get("/db", include_in_schema=False)
def db_health():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return {
                "status": "ok",
                "service": "db"
            }
