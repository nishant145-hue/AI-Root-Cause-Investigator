from app.agent.prompts import build_hypothesis_prompt


def test_hypothesis_prompt_contains_memory_quality_rules():

    prompt = build_hypothesis_prompt(
        incident_summary=(
            "Payment API error rate increased."
        ),
        evidence=[
            {
                "message": (
                    "Database connection timeout"
                )
            }
        ],
        historical_incidents=[
            {
                "investigation_id": 124,
                "similarity": 0.91,
                "memory_quality": 0.88,
                "memory_status": "RELIABLE",
                "confidence": 0.91,
                "root_cause": (
                    "Database connection pool exhaustion"
                ),
            }
        ],
    )

    assert "RELIABLE" in prompt
    assert "USEFUL" in prompt
    assert "WEAK" in prompt
    assert "STALE" in prompt

    assert "Memory quality" in prompt

    assert (
        "Current evidence is more important"
        in prompt
    )

    assert (
        "Historical memory is context, not proof."
        in prompt
    )
