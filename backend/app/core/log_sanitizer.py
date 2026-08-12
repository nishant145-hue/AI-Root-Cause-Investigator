import re
from typing import Any


SENSITIVE_PATTERNS = [
    # Authorization headers
    (
        re.compile(
            r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"
        ),
        r"\1[REDACTED]",
    ),

    # Password fields
    (
        re.compile(
            r"(?i)(password\s*[:=]\s*)[^\s,;]+"
        ),
        r"\1[REDACTED]",
    ),

    # API keys
    (
        re.compile(
            r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"
        ),
        r"\1[REDACTED]",
    ),

    # Secret keys
    (
        re.compile(
            r"(?i)(secret[_-]?key\s*[:=]\s*)[^\s,;]+"
        ),
        r"\1[REDACTED]",
    ),

    # Database URLs
    (
        re.compile(
            r"(?i)(postgres(?:ql)?://[^:\s]+:)[^@\s]+(@)"
        ),
        r"\1[REDACTED]\2",
    ),

    # JWT-looking values
    (
        re.compile(
            r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b"
        ),
        "[REDACTED_JWT]",
    ),
]


def sanitize_log_message(message: Any) -> str:
    """
    Remove known sensitive values from log messages.
    """

    text = str(message)

    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)

    return text