from app.services.llm.schemas import Evidence


def extract_evidence(
    logs: list[dict],
) -> list[dict]:
    """
    Convert relevant log results into structured evidence.

    The initial implementation identifies high-severity
    and error-related logs as evidence candidates.
    """

    evidence: list[dict] = []

    for log in logs:
        severity = str(log.get("severity", "")).upper()
        message = str(log.get("message", ""))
        raw_line = str(log.get("raw_line", ""))

        if severity not in {"ERROR", "CRITICAL"}:
            continue

        reason = (
            f"{severity} log from component "
            f"'{log.get('component', 'unknown')}'."
        )

        item = Evidence(
            log_line=raw_line or message,
            reason=reason,
        )

        evidence.append(item.model_dump())

    return evidence
