from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.rate_limit import limiter


def get_rate_limit_key(request: Request) -> str:
    return get_remote_address(request)


def rate_limit_login(request: Request) -> None:
    """
    Rate-limit authentication attempts.

    The actual limiting is handled explicitly by the
    application middleware/dependency layer.
    """
    return None