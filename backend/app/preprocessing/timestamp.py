from datetime import datetime


class TimestampNormalizer:
    """
    Normalize different timestamp formats into Python datetime.
    """

    SUPPORTED_FORMATS = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%b/%Y:%H:%M:%S",
        "%b %d %H:%M:%S",
    ]

    @classmethod
    def normalize(cls, timestamp):

        if timestamp is None:
            return None

        if isinstance(timestamp, datetime):
            return timestamp

        timestamp = str(timestamp).strip()

        for fmt in cls.SUPPORTED_FORMATS:

            try:
                dt = datetime.strptime(timestamp, fmt)

                if fmt == "%b %d %H:%M:%S":
                    dt = dt.replace(year=datetime.now().year)

                return dt

            except ValueError:
                continue

        return None