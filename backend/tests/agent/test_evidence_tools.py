from app.agent.tools.evidence import extract_evidence


def test_extract_evidence():

    logs = [
        {
            "severity": "ERROR",
            "component": "database",
            "message": "Database connection timeout",
            "raw_line": "ERROR database Database connection timeout",
        },
        {
            "severity": "INFO",
            "component": "payment-api",
            "message": "Payment request completed",
            "raw_line": "INFO payment-api Payment request completed",
        },
        {
            "severity": "CRITICAL",
            "component": "payment-api",
            "message": "Payment service unavailable",
            "raw_line": "CRITICAL payment-api Payment service unavailable",
        },
    ]

    evidence = extract_evidence(logs)

    assert len(evidence) == 2

    assert evidence[0]["log_line"] == (
        "ERROR database Database connection timeout"
    )

    assert evidence[1]["log_line"] == (
        "CRITICAL payment-api Payment service unavailable"
    )
