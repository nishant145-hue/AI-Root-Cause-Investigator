from unittest.mock import patch

import pytest

from app.agent.agents.reasoner import (
    ReasonerAgent,
)
from app.agent.schemas import (
    HypothesisAnalysisResponse,
    HypothesisResponse,
)


def test_reasoner_agent_name():
    agent = ReasonerAgent()

    assert agent.name == "reasoner"


def test_reasoner_agent_role():
    agent = ReasonerAgent()

    assert "hypoth" in agent.role.lower()


def test_reasoner_owns_hypothesis_generation():
    agent = ReasonerAgent()

    assert agent.owns_capability(
        "generate_hypotheses"
    )


def test_reasoner_does_not_own_log_search():
    agent = ReasonerAgent()

    assert not agent.owns_capability(
        "search_logs"
    )


def test_reasoner_does_not_own_memory_search():
    agent = ReasonerAgent()

    assert not agent.owns_capability(
        "semantic_memory_search"
    )


def test_reasoner_rejects_unowned_capability():
    agent = ReasonerAgent()

    with pytest.raises(PermissionError):
        agent.require_capability(
            "search_logs"
        )


def test_reasoner_generates_hypotheses():
    response = HypothesisAnalysisResponse(
        hypotheses=[
            HypothesisResponse(
                cause=(
                    "Database connection failure"
                ),
                confidence=0.82,
                supporting_evidence=[
                    "Database timeout"
                ],
                contradicting_evidence=[],
            )
        ]
    )

    with patch(
        "app.agent.agents.reasoner."
        "AgentReasoningService"
    ) as mock_service:

        mock_service.return_value.\
            generate_hypotheses.return_value = (
                response
            )

        agent = ReasonerAgent()

        result = agent.generate_hypotheses(
            incident_summary=(
                "Payment API errors increased"
            ),
            evidence=[
                {
                    "log_line": (
                        "Database connection timeout"
                    ),
                    "reason": (
                        "Database timeout indicates "
                        "connection failure"
                    ),
                }
            ],
            historical_incidents=[],
        )

        assert len(result.hypotheses) == 1

        assert (
            result.hypotheses[0].cause
            == "Database connection failure"
        )

        assert (
            result.hypotheses[0].confidence
            == 0.82
        )


def test_reasoner_run_without_evidence():
    agent = ReasonerAgent()

    result = agent.run(
        {
            "incident_summary": (
                "Payment API errors"
            ),
            "evidence": [],
            "historical_incidents": [],
        }
    )

    assert result["agent"] == "reasoner"

    assert result["status"] == "NO_EVIDENCE"

    assert result["hypotheses"] == []
