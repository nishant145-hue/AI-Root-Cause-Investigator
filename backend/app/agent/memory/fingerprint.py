import hashlib


def create_memory_fingerprint(
    summary: str,
    root_cause: str,
    failed_component: str | None,
) -> str:

    normalized = "|".join(
        [
            (summary or "").strip().lower(),
            (root_cause or "").strip().lower(),
            (failed_component or "").strip().lower(),
        ]
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()
