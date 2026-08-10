from repositories.admin_repo import (
    approve_pending_user,
    get_users_overview,
    reject_pending_user,
)


def get_all_users_service(conn):
    users = get_users_overview(conn)

    return {
        "success": True,
        "users": users
    }


def approve_user_service(conn, *, user_id: str) -> dict:
    updated = approve_pending_user(
        conn,
        user_id=user_id,
    )

    if not updated:
        return {
            "success": False,
            "message": "המשתמש לא נמצא או שאינו ממתין לאישור",
            "error_code": "USER_NOT_PENDING_APPROVAL",
        }

    return {
        "success": True,
        "message": "המשתמש אושר בהצלחה",
    }


def reject_user_service(conn, *, user_id: str) -> dict:
    updated = reject_pending_user(
        conn,
        user_id=user_id,
    )

    if not updated:
        return {
            "success": False,
            "message": "המשתמש לא נמצא או שאינו ממתין לאישור",
            "error_code": "USER_NOT_PENDING_APPROVAL",
        }

    return {
        "success": True,
        "message": "המשתמש נדחה",
    }
