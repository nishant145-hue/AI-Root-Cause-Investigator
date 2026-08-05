class ParserError(Exception):
    """Raised when a log parser cannot parse a file."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)