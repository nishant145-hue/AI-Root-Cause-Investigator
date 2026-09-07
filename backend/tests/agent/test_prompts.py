from app.agent.prompts import (
    build_hypothesis_prompt,
)


def test_hypothesis_prompt_includes_historical_context():

    prompt = build_hypothesis_prompt(
        incident_summary=(
            "Payment API error rate increased."
        ),
        evidence=[
            {
                "log_line": (
                    "Database connection timeout"
                ),
                "reason": (
                    "Database request failed"
                ),
            }
        ],
        historical_incidents=[
            {
                "investigation_id": 124,
                "similarity": 0.91,
                "summary": (
                    "Payment API database failure"
                ),
                "root_cause": (
                    "Database connection pool exhaustion"
                ),
                "failed_component": "payment-api",
                "severity": "HIGH",
                "confidence": 0.91,
            }
        ],
    )

    assert (
        "Database connection pool exhaustion"
        in prompt
    )

    assert (
        "historical"
        in prompt.lower()
    )

    assert (
        "current evidence"
        in prompt.lower()
    )
