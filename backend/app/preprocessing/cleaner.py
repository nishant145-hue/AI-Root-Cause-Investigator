import re


class MessageCleaner:
    """
    Cleans log messages before AI analysis.
    """

    @staticmethod
    def clean(message: str | None) -> str:
        if message is None:
            return ""

        message = str(message)

        # Remove control characters
        message = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", message)

        # Normalize line endings
        message = re.sub(r"[\t\r\n]+", " ", message)

        # Collapse spaces
        message = re.sub(r"\s+", " ", message)

        # Remove leading/trailing spaces
        message = message.strip()

        # Remove repeated punctuation
        message = re.sub(r"\.{2,}", ".", message)
        message = re.sub(r"\-{2,}", "-", message)
        message = re.sub(r"\={2,}", "=", message)

        return message