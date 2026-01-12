# auth/jwt.py
import os
import time
import jwt

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ISSUER = os.environ.get("JWT_ISSUER", "kosherpay")

ACCESS_TTL_MIN = int(os.environ.get("JWT_ACCESS_TTL_MIN", "30"))
REFRESH_TTL_DAYS = int(os.environ.get("JWT_REFRESH_TTL_DAYS", "14"))

def _now() -> int:
    return int(time.time())

def create_access_token(*, user_id: str, role: str, phone_number: str | None = None) -> str:
    iat = _now()
    exp = iat + ACCESS_TTL_MIN * 60
    payload = {
        "iss": JWT_ISSUER,
        "iat": iat,
        "exp": exp,
        "type": "access",
        "sub": user_id,
        "role": role,
        "phone": phone_number,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def create_refresh_token(*, user_id: str) -> str:
    iat = _now()
    exp = iat + REFRESH_TTL_DAYS * 24 * 60 * 60
    payload = {
        "iss": JWT_ISSUER,
        "iat": iat,
        "exp": exp,
        "type": "refresh",
        "sub": user_id,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"], issuer=JWT_ISSUER)
