import hashlib
import secrets


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure refresh token.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token before storing it.
    """
    return hashlib.sha256(
        token.encode()
    ).hexdigest()