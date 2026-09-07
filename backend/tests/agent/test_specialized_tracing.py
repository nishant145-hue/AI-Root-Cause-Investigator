from unittest.mock import Mock, patch

from app.agent.agents.investigator import (
    InvestigatorAgent,
)
from app.agent.agents.memory import (
    MemoryAgent,
)
from app.agent.agents.reasoner import (
    ReasonerAgent,
)


def test_investigator_records_trace():

    agent = InvestigatorAgent()

    session = Mock()

    with patch(
        "app.agent.agents.investigator.search_logs",
        return_value=[
            {"id": 1},
            {"id": 2},
        ],
    ):

        result = agent.search_logs(
            session=session,
            log_file_id=1,
        )

    assert len(result) == 2

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["agent"] == "investigator"
    assert trace["action"] == "search_logs"
    assert trace["status"] == "COMPLETED"

    assert trace["metadata"][
        "result_count"
    ] == 2

    assert trace["duration_ms"] >= 0


def test_investigator_records_failure():

    agent = InvestigatorAgent()

    session = Mock()

    with patch(
        "app.agent.agents.investigator.search_logs",
        side_effect=RuntimeError(
            "database unavailable"
        ),
    ):

        try:
            agent.search_logs(
                session=session,
                log_file_id=1,
            )
        except RuntimeError:
            pass

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["status"] == "FAILED"

    assert (
        trace["error"]
        == "database unavailable"
    )


def test_memory_semantic_search_trace():

    agent = MemoryAgent()

    with patch(
        "app.agent.agents.memory.InvestigationRetriever"
    ) as retriever_cls:

        retriever = retriever_cls.return_value

        retriever.search.return_value = [
            {"id": 1},
        ]

        result = agent.semantic_search(
            query="database timeout",
            user_id=10,
        )

    assert len(result) == 1

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["agent"] == "memory"

    assert trace["action"] == (
        "semantic_memory_search"
    )

    assert trace["status"] == "COMPLETED"

    assert trace["metadata"][
        "user_id"
    ] == 10


def test_reasoner_trace():

    agent = ReasonerAgent()

    mock_response = Mock()

    mock_response.hypotheses = [
        Mock(),
        Mock(),
    ]

    with patch(
        "app.agent.agents.reasoner.AgentReasoningService"
    ) as service_cls:

        service = service_cls.return_value

        service.generate_hypotheses.return_value = (
            mock_response
        )

        result = agent.generate_hypotheses(
            incident_summary="API timeout",
            evidence=[
                {"message": "timeout"},
            ],
            historical_incidents=[],
        )

    assert result == mock_response

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["agent"] == "reasoner"

    assert trace["action"] == (
        "generate_hypotheses"
    )

    assert trace["status"] == "COMPLETED"

    assert trace["metadata"][
        "evidence_count"
    ] == 1

    assert trace["metadata"][
        "hypothesis_count"
    ] == 2

from app.agent.agents.validator import (
    ValidatorAgent,
)


def test_validator_records_successful_trace():

    agent = ValidatorAgent()

    hypotheses = [
        {
            "cause": "Database connection failure",
            "confidence": 0.95,
            "supporting_evidence": [
                "Connection timeout"
            ],
            "contradicting_evidence": [],
        }
    ]

    evidence = [
        {
            "message": "Database timeout"
        }
    ]

    result = agent.validate_root_cause(
        hypotheses=hypotheses,
        evidence=evidence,
    )

    assert result["validated"] is True

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["agent"] == "validator"

    assert trace["action"] == (
        "validate_root_cause"
    )

    assert trace["status"] == "COMPLETED"

    assert trace["metadata"][
        "hypothesis_count"
    ] == 1

    assert trace["metadata"][
        "evidence_count"
    ] == 1

    assert trace["metadata"][
        "validation_status"
    ] == "ROOT_CAUSE_VALIDATED"

    assert trace["metadata"][
        "confidence"
    ] == 0.95


def test_validator_records_rejection_trace():

    agent = ValidatorAgent()

    hypotheses = [
        {
            "cause": "Unknown failure",
            "confidence": 0.4,
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }
    ]

    result = agent.validate_root_cause(
        hypotheses=hypotheses,
        evidence=[],
    )

    assert result["validated"] is False

    assert result["status"] == "REJECTED"

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["status"] == "COMPLETED"

    assert trace["metadata"][
        "validation_status"
    ] == "REJECTED"


def test_validator_records_more_evidence_required():

    agent = ValidatorAgent()

    result = agent.validate_root_cause(
        hypotheses=[],
        evidence=[],
    )

    assert result["validated"] is False

    assert result["status"] == (
        "MORE_EVIDENCE_REQUIRED"
    )

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["status"] == "COMPLETED"

    assert trace["metadata"][
        "validation_status"
    ] == "MORE_EVIDENCE_REQUIRED"
