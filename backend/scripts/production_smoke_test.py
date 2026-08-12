import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = os.getenv("SMOKE_TEST_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = float(os.getenv("SMOKE_TEST_TIMEOUT", "10"))


def check_endpoint(path: str, expected_status: int = 200) -> bool:
    url = f"{BASE_URL}{path}"

    try:
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "AI-Root-Cause-Investigator-Smoke-Test"},
        )

        with urlopen(request, timeout=TIMEOUT) as response:
            status = response.status
            response.read()

        if status != expected_status:
            print(f"FAIL  {path} -> HTTP {status} (expected {expected_status})")
            return False

        print(f"PASS  {path} -> HTTP {status}")
        return True

    except HTTPError as exc:
        print(f"FAIL  {path} -> HTTP {exc.code}")
        return False

    except URLError as exc:
        print(f"FAIL  {path} -> connection error: {exc.reason}")
        return False

    except Exception as exc:
        print(f"FAIL  {path} -> {type(exc).__name__}: {exc}")
        return False


def main() -> int:
    print("AI Root Cause Investigator - Production Smoke Test")
    print(f"Base URL: {BASE_URL}")
    print()

    checks = [
        ("/health", 200),
        ("/ready", 200),
        ("/", 200),
        ("/docs", 200),
    ]

    results = [
        check_endpoint(path, expected_status)
        for path, expected_status in checks
    ]

    print()

    if all(results):
        print("SMOKE TEST: PASS")
        return 0

    print("SMOKE TEST: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())