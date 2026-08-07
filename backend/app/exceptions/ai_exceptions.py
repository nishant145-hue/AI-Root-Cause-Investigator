class AIError(Exception):
    """Base exception for all AI-related errors."""


class AIConnectionError(AIError):
    """Raised when the AI provider cannot be reached."""


class AIRateLimitError(AIError):
    """Raised when the AI provider rate limit is exceeded."""


class AIResponseError(AIError):
    """Raised when the AI provider returns an invalid response."""


class AIValidationError(AIError):
    """Raised when AI output fails validation."""