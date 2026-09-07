from sqlmodel import Session

from app.services.parsed_log_service import ParsedLogService


def search_logs(
    session: Session,
    log_file_id: int,
    query: str | None = None,
    severity: str | None = None,
    component: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    Search parsed logs for an investigation.

    Filters:
        query      - Searches message/raw log content.
        severity   - Filters by severity.
        component  - Filters by component.
        limit      - Maximum number of results.
    """

    logs = ParsedLogService.get_logs(
        session=session,
        log_file_id=log_file_id,
    )

    results = []

    normalized_query = query.lower() if query else None
    normalized_severity = severity.upper() if severity else None
    normalized_component = component.lower() if component else None

    for log in logs:

        if (
            normalized_severity
            and log.severity.upper() != normalized_severity
        ):
            continue

        if (
            normalized_component
            and normalized_component not in log.component.lower()
        ):
            continue

        if normalized_query:
            searchable_text = (
                f"{log.message} "
                f"{log.raw_line} "
                f"{log.source} "
                f"{log.component}"
            ).lower()

            if normalized_query not in searchable_text:
                continue

        results.append(
            {
                "id": str(log.id),
                "timestamp": (
                    log.timestamp.isoformat()
                    if log.timestamp
                    else None
                ),
                "severity": log.severity,
                "source": log.source,
                "component": log.component,
                "message": log.message,
                "raw_line": log.raw_line,
            }
        )

        if len(results) >= limit:
            break

    return results
