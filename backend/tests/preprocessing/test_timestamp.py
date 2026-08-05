from app.preprocessing.timestamp import TimestampNormalizer


samples = [
    "2026-08-04T10:15:30",
    "2026-08-04 10:15:30",
    "04/Aug/2026:10:15:30",
    "Aug 04 10:15:30",
]

for value in samples:

    print(value)

    print(TimestampNormalizer.normalize(value))

    print("-" * 40)