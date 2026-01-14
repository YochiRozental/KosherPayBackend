import bcrypt
import logging

from typing import Final

logger = logging.getLogger(__name__)

_ENCODING: Final[str] = "utf-8"

def verify_secret(secret: str, secret_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            secret.strip().encode(_ENCODING),
            secret_hash.encode(_ENCODING),
        )
    except (ValueError, TypeError) as e:
        logger.warning("bcrypt verification failed: %s", e)
        return False

def hash_secret(secret: str) -> str:
    return bcrypt.hashpw(
        secret.strip().encode(_ENCODING),
        bcrypt.gensalt(),
    ).decode(_ENCODING)
