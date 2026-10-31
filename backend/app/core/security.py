import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import JWT_SECRET

ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "purpose": "login", "exp": expires}, JWT_SECRET, algorithm="HS256")


def read_token(token: str) -> int | None:
    payload = _decode(token)
    if not payload or payload.get("purpose", "login") != "login":
        return None
    return int(payload["sub"])


def create_upload_token(candidate_id: int, company_id: int) -> str:
    """The token in a candidate's upload link. It can never be used to log in."""
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    payload = {"sub": str(candidate_id), "company": company_id, "purpose": "upload", "exp": expires}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def read_upload_token(token: str) -> tuple[int, int] | None:
    """Returns (candidate_id, company_id), or None if the token is not a valid upload token."""
    payload = _decode(token)
    if not payload or payload.get("purpose") != "upload":
        return None
    return int(payload["sub"]), int(payload["company"])


def _decode(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        int(payload["sub"])
        return payload
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
