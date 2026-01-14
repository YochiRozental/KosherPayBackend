from functools import wraps
from flask import request, jsonify, g

from auth.jwt_utils import decode_token, ExpiredTokenError, InvalidTokenError

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({
                "success": False,
                "message": "Missing Bearer token"
            }), 401

        token = auth.split(" ", 1)[1].strip()

        try:
            payload = decode_token(token)
        except ExpiredTokenError:
            return jsonify({"success": False, "message": "Token expired"}), 401
        except InvalidTokenError:
            return jsonify({"success": False, "message": "Invalid token"}), 401

        if payload.get("type") != "access":
            return jsonify({
                "success": False,
                "message": "Invalid token type"
            }), 401

        g.user = {
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "phone": payload.get("phone"),
        }

        return fn(*args, **kwargs)

    return wrapper

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not getattr(g, "user", None):
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        if g.user.get("role") != "admin":
            return jsonify({"success": False, "message": "Forbidden"}), 403
        return fn(*args, **kwargs)
    return wrapper
