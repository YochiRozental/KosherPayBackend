from repositories.admin_repo import get_users_overview


def get_all_users_service(conn):
    users = get_users_overview(conn)

    return {
        "success": True,
        "users": users
    }