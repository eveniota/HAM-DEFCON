import time
import jwt
from .crypto import get_private_key_pem, get_public_key_pem

JWT_ISSUER = "sentinelauth-sso"

def create_user_jwt(user_id: int, username: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "iss": JWT_ISSUER,
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + 7200,  # 2 hours validity
    }
    return jwt.encode(payload, get_private_key_pem(), algorithm="RS256")

def verify_user_jwt(token: str) -> dict:
    public_pem = get_public_key_pem()
    try:
        payload = jwt.decode(
            token,
            public_pem,
            algorithms=["RS256", "HS256"],  # <-- The Vulnerability
            issuer=JWT_ISSUER,
        )
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Token validation failed: {str(e)}")