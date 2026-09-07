from datetime import datetime, timedelta, timezone

from app.agent.memory.constants import (
    MEMORY_ACTIVE,
    MEMORY_STALE,
    MEMORY_ARCHIVED,
    STALE_MEMORY_DAYS,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_memory_stale(
    last_verified_at: str | None,
    stale_days: int = STALE_MEMORY_DAYS,
) -> bool:
    if not last_verified_at:
        return True

    try:
        verified_at = datetime.fromisoformat(
            last_verified_at
        )

        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(
                tzinfo=timezone.utc
            )

        return (
            utc_now() - verified_at
        ) > timedelta(days=stale_days)

    except (TypeError, ValueError):
        return True


def calculate_memory_status(
    last_verified_at: str | None,
) -> str:

    if is_memory_stale(last_verified_at):
        return MEMORY_STALE

    return MEMORY_ACTIVE
