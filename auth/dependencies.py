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
) -> dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise _unauthorized("Missing Bearer token")

    token = credentials.credentials

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
    role = payload.get("role")

    if not user_id or not role:
        logger.warning("Token payload missing sub/role")
        raise _unauthorized("Invalid token")

    return {
        "user_id": str(user_id),
        "role": role,
        "phone": payload.get("phone"),
    }

async def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Forbidden"},
        )
    return current_user
