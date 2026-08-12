from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for notification retries."""

    max_retries: int = 3
    base_delay_seconds: int = 2
    max_delay_seconds: int = 60

    def calculate_delay(self, retry_count: int) -> int:
        """Calculate exponential backoff delay."""

        if retry_count <= 0:
            return 0

        delay = self.base_delay_seconds * (2 ** (retry_count - 1))

        return min(
            delay,
            self.max_delay_seconds,
        )

    def can_retry(self, retry_count: int) -> bool:
        """Return whether another retry is allowed."""

        return retry_count < self.max_retries