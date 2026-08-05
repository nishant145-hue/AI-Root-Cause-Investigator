from app.preprocessing.cleaner import MessageCleaner

samples = [
    " ERROR    Database timeout ",
    "INFO\tApplication Started",
    "Server\x00 started",
    "User\nLogin",
    "Multiple     Spaces",
    "Line1\r\nLine2",
    "",
    None,
]

for sample in samples:
    print(f"Original : {repr(sample)}")
    print(f"Cleaned  : {repr(MessageCleaner.clean(sample))}")
    print("-" * 50)