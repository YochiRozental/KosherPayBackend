from __future__ import annotations

import os
import time
import jwt as pyjwt

from typing import Any, Mapping, Optional

# =========================
# Config
# =========================

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing in environment variables")

JWT_ISSUER = os.environ.get("JWT_ISSUER", "kosherpay")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

ACCESS_TTL_MIN = int(os.environ.get("JWT_ACCESS_TTL_MIN", "30"))
REFRESH_TTL_DAYS = int(os.environ.get("JWT_REFRESH_TTL_DAYS", "14"))

def _now() -> int:
    return int(time.time())

# =========================
# Project exceptions
# =========================

class JWTError(Exception):
    """Base JWT exception for this project."""

class InvalidTokenError(JWTError):
    """Token is invalid (bad signature, malformed, wrong issuer, etc.)."""

class ExpiredTokenError(JWTError):
    """Token has expired."""

class InvalidTokenTypeError(JWTError):
    """Token 'type' claim is missing/invalid."""

# =========================
# Token creation
# =========================

def create_access_token(*, user_id: str, role: str, phone_number: Optional[str] = None) -> str:
    iat = _now()
    exp = iat + ACCESS_TTL_MIN * 60

    payload: dict[str, Any] = {
        "iss": JWT_ISSUER,
        "iat": iat,
        "exp": exp,
        "type": "access",
        "sub": user_id,
        "role": role,
    }

    if phone_number:
        payload["phone"] = phone_number

    token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token.decode("utf-8") if isinstance(token, bytes) else token

def create_refresh_token(*, user_id: str) -> str:
    iat = _now()
    exp = iat + REFRESH_TTL_DAYS * 24 * 60 * 60

    payload: dict[str, Any] = {
        "iss": JWT_ISSUER,
        "iat": iat,
        "exp": exp,
        "type": "refresh",
        "sub": user_id,
    }

    token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token.decode("utf-8") if isinstance(token, bytes) else token

# =========================
# Token decoding / validation
# =========================

def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = pyjwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub", "type"]},
        )
    except pyjwt.ExpiredSignatureError as e:
        raise ExpiredTokenError("Token expired") from e
    except pyjwt.InvalidIssuerError as e:
        raise InvalidTokenError("Invalid issuer") from e
    except pyjwt.InvalidAlgorithmError as e:
        raise InvalidTokenError("Invalid algorithm") from e
    except pyjwt.DecodeError as e:
        raise InvalidTokenError("Decode error") from e
    except pyjwt.InvalidTokenError as e:
        raise InvalidTokenError("Invalid token") from e

    if not isinstance(payload, Mapping):
        raise InvalidTokenError("Invalid payload type")

    return dict(payload)

def require_token_type(payload: Mapping[str, Any], expected: str) -> None:
    t = payload.get("type")
    if t != expected:
        raise InvalidTokenTypeError(
            f"Invalid token type: expected '{expected}', got '{t}'"
        )
