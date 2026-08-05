from pathlib import Path


class ParserDetector:
    """
    Detects the appropriate parser for an uploaded log file.
    """

    EXTENSION_MAP = {
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "txt",
        ".log": "log",
        ".csv": "csv",
    }

    @classmethod
    def detect(cls, filename: str) -> str:
        extension = Path(filename).suffix.lower()

        return cls.EXTENSION_MAP.get(extension, "generic")