import hashlib
import hmac
import os

SECRET_KEY = os.getenv("SECRET_KEY", "docuvault_master_secret_2026_xyz").encode()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def sign_token(identifier: str | int) -> str:
    return hmac.new(SECRET_KEY, str(identifier).encode(), hashlib.sha256).hexdigest()


def verify_token(identifier: str | int, signature: str) -> bool:
    expected = sign_token(identifier)
    return hmac.compare_digest(expected, signature)
