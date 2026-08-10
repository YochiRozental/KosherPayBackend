from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.jwt_utils import (
    decode_token,
    require_token_type,
    ExpiredTokenError,
    InvalidTokenError,
    InvalidTokenTypeError,
)
from db.deps import get_db
from repositories.users_repo import get_user_auth_state_by_id

logger = logging.getLogger("kosherpay.auth")
security = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Security(security),
        conn=Depends(get_db),
) -> dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise _unauthorized("Missing Bearer token")

    token: str = str(credentials.credentials)

    try:
        payload = decode_token(token)
        require_token_type(payload, "access")
    except ExpiredTokenError:
        logger.info("Expired access token")
        raise _unauthorized("Token expired")
    except InvalidTokenTypeError:
        logger.info("Invalid token type")
        raise _unauthorized("Invalid token")
    except InvalidTokenError:
        logger.info("Invalid token")
        raise _unauthorized("Invalid token")

    user_id = payload.get("sub")

    if not user_id:
        logger.warning("Token payload missing sub")
        raise _unauthorized("Invalid token")

    user = get_user_auth_state_by_id(
        conn,
        user_id=str(user_id),
    )

    if not user:
        logger.info("User not found or deleted")
        raise _unauthorized("User is not active")

    if user["status"] != "active":
        logger.info(
            "Inactive user attempted authenticated request: user_id=%s status=%s",
            user_id,
            user["status"],
        )
        raise _unauthorized("User is not active")

    return {
        "user_id": str(user["user_id"]),
        "role": user["role"],
        "phone": payload.get("phone"),
    }


async def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Forbidden"},
        )
    return current_user
