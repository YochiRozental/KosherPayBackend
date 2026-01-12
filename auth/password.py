import bcrypt

# def hash_secret(secret: str) -> str:
#     secret = secret.strip()
#     hashed = bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt(rounds=12))
#     return hashed.decode("utf-8")
#
def verify_secret(secret: str, secret_hash: str) -> bool:
    try:
        return bcrypt.checkpw(secret.strip().encode("utf-8"), secret_hash.encode("utf-8"))
    except Exception:
        return False

def hash_secret(secret: str) -> str:
    return bcrypt.hashpw(
        secret.strip().encode(),
        bcrypt.gensalt()
    ).decode()
