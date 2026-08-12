from fastapi import Request

from app.core.rate_limit import limiter


def login_rate_limit(request: Request) -> None:
    limiter.hit("5/minute", request)


def register_rate_limit(request: Request) -> None:
    limiter.hit("5/minute", request)


def refresh_rate_limit(request: Request) -> None:
    limiter.hit("10/minute", request)


def logout_rate_limit(request: Request) -> None:
    limiter.hit("20/minute", request)