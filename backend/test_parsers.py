from pathlib import Path

from app.parsers.parser_factory import ParserFactory

SAMPLE_DIR = Path("tests/sample_logs")

files = [
    "sample.json",
    "sample.yaml",
    "sample.txt",
    "sample.log",
]

for filename in files:
    print("=" * 60)
    print(f"Testing: {filename}")

    parser = ParserFactory.get_parser(filename)
    logs = parser.parse(SAMPLE_DIR / filename)

    print(f"Parser: {parser.__class__.__name__}")
    print(f"Total Logs: {len(logs)}")

    for log in logs:
        print(log)

    print()