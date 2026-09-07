from types import SimpleNamespace

from app.agent.memory.historical import (
    search_historical_incidents,
)


def test_historical_memory_returns_similar_incident(
    monkeypatch,
):

    historical = SimpleNamespace(
        id=124,
        user_id=1,
        status="COMPLETED",
        title="Payment API database timeout",
        description=(
            "Payment API experienced database "
            "connection problems."
        ),
        summary=(
            "Payment API database connection failures."
        ),
        root_cause=(
            "Database connection pool exhaustion"
        ),
        failed_component="payment-api",
        severity="HIGH",
        confidence=0.91,
    )

    class FakeResult:
        def all(self):
            return [historical]

    class FakeSession:

        def exec(self, statement):
            return FakeResult()

    results = search_historical_incidents(
        session=FakeSession(),
        current_investigation_id=1,
        user_id=1,
        incident_summary=(
            "Payment API database connection failure"
        ),
        limit=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result["investigation_id"] == 124

    assert result["root_cause"] == (
        "Database connection pool exhaustion"
    )

    assert result["failed_component"] == (
        "payment-api"
    )

    assert result["similarity"] > 0
