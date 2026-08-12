import logging
import sys
from pathlib import Path

from loguru import logger

from app.core.log_sanitizer import sanitize_log_message


# -------------------------------------------------------------------
# Log directory
# -------------------------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


# -------------------------------------------------------------------
# Remove Loguru's default handler
# -------------------------------------------------------------------

logger.remove()

logger.configure(
    extra={"request_id": "-"},
)

# -------------------------------------------------------------------
# Safe sink
# -------------------------------------------------------------------

def _safe_sink(message):
    """
    Sanitize the final log message before writing it anywhere.

    This provides a final defense against accidental leakage of:
    - passwords
    - API keys
    - secret keys
    - database credentials
    - bearer tokens
    - JWTs
    """

    sanitized = sanitize_log_message(str(message))
    print(sanitized, end="")


# -------------------------------------------------------------------
# Console logging
# -------------------------------------------------------------------

logger.add(
    sink=_safe_sink,
    level="INFO",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level} | "
        "request_id={extra[request_id]} | "
        "{name}:{function}:{line} - "
        "{message}"
    ),
)


# -------------------------------------------------------------------
# Application log file
# -------------------------------------------------------------------

logger.add(
    LOG_DIR / "app.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="INFO",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level} | "
        "request_id={extra[request_id]} | "
        "{message}"
    ),
    filter=lambda record: True,
)


# -------------------------------------------------------------------
# Error log file
# -------------------------------------------------------------------

logger.add(
    LOG_DIR / "error.log",
    rotation="5 MB",
    retention="30 days",
    compression="zip",
    level="ERROR",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level} | "
        "request_id={extra[request_id]} | "
        "{message}"
    ),
)


# -------------------------------------------------------------------
# Standard-library logging
# -------------------------------------------------------------------

__all__ = ["logger"]


def setup_logging() -> None:
    """
    Configure standard-library logging.

    Loguru is used by the application for structured application
    logging. Standard-library logging remains available for libraries
    that use Python's logging module.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )