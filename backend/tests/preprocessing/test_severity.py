from app.preprocessing.severity import SeverityNormalizer

samples = [
    "INFO",
    "info",
    "Information",
    "Warn",
    "WARNING",
    "warn",
    "ERROR",
    "Err",
    "exception",
    "Fatal",
    "panic",
    "DEBUG",
    "trace",
    None,
    "random",
]

for item in samples:
    print(f"{item} --> {SeverityNormalizer.normalize(item)}")