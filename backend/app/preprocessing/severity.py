from app.enums.severity import SeverityLevel


class SeverityNormalizer:
    """
    Normalize log severity values into SeverityLevel enum.
    """

    SEVERITY_MAP = {
        # DEBUG
        "debug": SeverityLevel.DEBUG,
        "trace": SeverityLevel.DEBUG,

        # INFO
        "info": SeverityLevel.INFO,
        "information": SeverityLevel.INFO,
        "informational": SeverityLevel.INFO,

        # WARNING
        "warn": SeverityLevel.WARNING,
        "warning": SeverityLevel.WARNING,

        # ERROR
        "error": SeverityLevel.ERROR,
        "err": SeverityLevel.ERROR,
        "exception": SeverityLevel.ERROR,

        # CRITICAL
        "critical": SeverityLevel.CRITICAL,
        "fatal": SeverityLevel.CRITICAL,
        "panic": SeverityLevel.CRITICAL,
    }

    @classmethod
    def normalize(cls, severity):

        if severity is None:
            return SeverityLevel.UNKNOWN

        if isinstance(severity, SeverityLevel):
            return severity

        severity = str(severity).strip().lower()

        return cls.SEVERITY_MAP.get(
            severity,
            SeverityLevel.UNKNOWN,
        )