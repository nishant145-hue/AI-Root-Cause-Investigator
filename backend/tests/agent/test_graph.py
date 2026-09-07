from app.agent.graph import build_investigation_graph
from app.agent.schemas import (
    HypothesisAnalysisResponse,
    HypothesisResponse,
)


# ---------------------------------------------------------
# Capture historical context passed to the reasoner
# ---------------------------------------------------------

captured_context = {}


# ---------------------------------------------------------
# Mock LLM reasoning
# ---------------------------------------------------------

def fake_generate_hypotheses(
    self,
    incident_summary,
    evidence,
    historical_incidents=None,
):
    captured_context["historical_incidents"] = (
        historical_incidents
    )

    return HypothesisAnalysisResponse(
        hypotheses=[
            HypothesisResponse(
                cause="Database connection failure",
                confidence=0.82,
                supporting_evidence=[
                    "Database connection timeout",
                ],
                contradicting_evidence=[],
            ),
            HypothesisResponse(
                cause="Application-level failure",
                confidence=0.35,
                supporting_evidence=[
                    "Payment API error rate increased",
                ],
                contradicting_evidence=[],
            ),
        ]
    )


def test_investigation_graph(monkeypatch):

    # ---------------------------------------------------------
    # Mock logs
    # ---------------------------------------------------------

    logs = [
        {
            "id": "1",
            "timestamp": None,
            "severity": "ERROR",
            "source": "application",
            "component": "database",
            "message": "Database connection timeout",
            "raw_line": (
                "ERROR database "
                "Database connection timeout"
            ),
        }
    ]

    # ---------------------------------------------------------
    # Mock historical memory
    # ---------------------------------------------------------

    def fake_search_historical_incidents(
        session,
        current_investigation_id,
        user_id,
        incident_summary,
        limit=5,
    ):
        return [
            {
                "investigation_id": 124,
                "similarity": 0.91,
                "summary": (
                    "Payment API experienced "
                    "database connection failures."
                ),
                "root_cause": (
                    "Database connection pool exhaustion"
                ),
                "failed_component": "payment-api",
                "severity": "HIGH",
                "confidence": 0.91,
            }
        ]

    monkeypatch.setattr(
        "app.agent.nodes.memory.search_historical_incidents",
        fake_search_historical_incidents,
    )

    # ---------------------------------------------------------
    # Mock log search
    # ---------------------------------------------------------

    def fake_search_logs(
        session,
        log_file_id,
        query=None,
        severity=None,
        component=None,
        limit=50,
    ):
        return logs

    monkeypatch.setattr(
        "app.agent.nodes.investigator.search_logs",
        fake_search_logs,
    )

    # ---------------------------------------------------------
    # Mock LLM reasoning
    # ---------------------------------------------------------

    monkeypatch.setattr(
        "app.agent.nodes.reasoner.AgentReasoningService"
        ".generate_hypotheses",
        fake_generate_hypotheses,
    )

    # ---------------------------------------------------------
    # Build graph
    # ---------------------------------------------------------

    graph = build_investigation_graph(
        session=None,
    )

    # ---------------------------------------------------------
    # Initial state
    # ---------------------------------------------------------

    initial_state = {
        "investigation_id": 1,
        "user_id": 1,
        "log_file_id": 1,

        "incident_summary": (
            "Payment API error rate increased."
        ),

        "plan": [],
        "current_step": "",
        "next_action": None,

        "observations": [],
        "evidence": [],

        "historical_incidents": [],

        "hypotheses": [],
        "tool_calls": [],
        "tool_results": [],
        "remaining_questions": [],

        "confidence": None,
        "root_cause": None,
        "failed_component": None,

        "investigation_attempts": 0,

        "investigation_status": "STARTING",
    }

    # ---------------------------------------------------------
    # Execute graph
    # ---------------------------------------------------------

    result = graph.invoke(initial_state)

    # =========================================================
    # Final investigation status
    # =========================================================

    assert result["investigation_status"] == (
        "ROOT_CAUSE_VALIDATED"
    )

    # =========================================================
    # Final confidence
    # =========================================================

    assert result["confidence"] == 0.82

    # =========================================================
    # Root cause
    # =========================================================

    assert result["root_cause"] == (
        "Database connection failure"
    )

    # =========================================================
    # Investigation attempts
    # =========================================================

    assert result["investigation_attempts"] <= 3

    # =========================================================
    # Dynamic planning
    # =========================================================

    assert len(result["plan"]) >= 3

    # =========================================================
    # Observations
    # =========================================================

    assert len(result["observations"]) == (
        result["investigation_attempts"]
    )

    # =========================================================
    # Tool calls
    # =========================================================

    assert len(result["tool_calls"]) == (
        result["investigation_attempts"]
    )

    # =========================================================
    # Tool results
    # =========================================================

    assert len(result["tool_results"]) == (
        result["investigation_attempts"]
    )

    # =========================================================
    # Evidence
    # =========================================================

    assert len(result["evidence"]) == 1

    # =========================================================
    # Historical memory
    # =========================================================

    assert len(
        result["historical_incidents"]
    ) == 1

    historical = result[
        "historical_incidents"
    ][0]

    assert historical["investigation_id"] == 124

    assert historical["similarity"] == 0.91

    assert historical["root_cause"] == (
        "Database connection pool exhaustion"
    )

    assert historical["failed_component"] == (
        "payment-api"
    )

    # =========================================================
    # Verify historical context reached the LLM reasoner
    # =========================================================

    assert (
        "historical_incidents"
        in captured_context
    )

    assert len(
        captured_context[
            "historical_incidents"
        ]
    ) == 1

    captured_historical = captured_context[
        "historical_incidents"
    ][0]

    assert (
        captured_historical[
            "investigation_id"
        ]
        == 124
    )

    assert (
        captured_historical[
            "similarity"
        ]
        == 0.91
    )

    assert (
        captured_historical[
            "root_cause"
        ]
        == "Database connection pool exhaustion"
    )

    # =========================================================
    # Hypotheses
    # =========================================================

    assert len(result["hypotheses"]) == 2

    # ---------------------------------------------------------
    # Strongest hypothesis
    # ---------------------------------------------------------

    hypothesis = result["hypotheses"][0]

    assert hypothesis["cause"] == (
        "Database connection failure"
    )

    assert hypothesis["confidence"] == 0.82

    assert hypothesis["status"] == "VALIDATED"

    # ---------------------------------------------------------
    # Alternative hypothesis
    # ---------------------------------------------------------

    alternative = result["hypotheses"][1]

    assert alternative["cause"] == (
        "Application-level failure"
    )

    assert alternative["confidence"] == 0.35
