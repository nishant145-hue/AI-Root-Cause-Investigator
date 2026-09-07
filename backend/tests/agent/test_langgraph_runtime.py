from unittest.mock import MagicMock, patch

import pytest
from app.agent.langgraph_runtime import (
    _build_initial_state,
    _map_evidence,
)


def test_build_initial_state():
    state = _build_initial_state(
        investigation_id=10,
        user_id=20,
        log_file_id=30,
        incident_summary="Database timeout",
    )

    assert state["investigation_id"] == 10
    assert state["user_id"] == 20
    assert state["log_file_id"] == 30
    assert state["incident_summary"] == "Database timeout"

    assert state["investigation_attempts"] == 0
    assert state["investigation_status"] == "STARTING"
    assert state["evidence"] == []
    assert state["hypotheses"] == []
    assert state["execution_timeline"] == []
    assert state["execution_analytics"] == {}


def test_map_evidence():
    state = {
        "evidence": [
            {
                "log_line": "database connection timeout",
                "reason": "Database connection failed",
            }
        ]
    }

    result = _map_evidence(state)

    assert len(result) == 1
    assert result[0].log_line == (
        "database connection timeout"
    )
    assert result[0].reason == (
        "Database connection failed"
    )

from unittest.mock import MagicMock, patch

from app.agent.langgraph_runtime import (
    LangGraphInvestigationError,
    _map_final_state,
    run_langgraph_investigation,
)


def test_map_final_state():
    state = {
        "investigation_status": "ROOT_CAUSE_VALIDATED",
        "incident_summary": "Database timeout",
        "summary": "Database investigation completed.",
        "root_cause": "Connection pool exhausted",
        "failed_component": "Database",
        "severity": "Critical",
        "confidence": 0.95,
        "evidence": [
            {
                "log_line": "connection pool exhausted",
                "reason": "Database connections were unavailable.",
            }
        ],
        "hypotheses": [
            {
                "cause": "Connection pool exhausted",
                "confidence": 0.95,
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "status": "VALIDATED",
            }
        ],
        "remaining_questions": [],
    }

    result = _map_final_state(state)

    assert result.summary == (
        "Database investigation completed."
    )
    assert result.root_cause == (
        "Connection pool exhausted"
    )
    assert result.failed_component == "Database"
    assert result.severity == "Critical"
    assert result.confidence == 0.95
    assert len(result.evidence) == 1
    assert len(result.recommendations) == 1


def test_map_final_state_rejects_unvalidated_result():
    state = {
        "investigation_status": "FAILED",
        "root_cause": "Something",
        "confidence": 0.5,
    }

    with pytest.raises(
        LangGraphInvestigationError
    ):
        _map_final_state(state)

def test_map_final_state_preserves_component_and_severity():
    state = {
        "investigation_status": "ROOT_CAUSE_VALIDATED",
        "incident_summary": "Database outage",
        "summary": "Database investigation completed.",
        "root_cause": "Connection pool exhausted",
        "failed_component": "database",
        "severity": "CRITICAL",
        "confidence": 0.95,
        "evidence": [
            {
                "log_line": "database connection pool exhausted",
                "reason": "CRITICAL log from component 'database'.",
            }
        ],
        "hypotheses": [],
        "remaining_questions": [],
    }

    result = _map_final_state(state)

    assert result.failed_component == "database"
    assert result.severity == "CRITICAL"
    assert result.root_cause == "Connection pool exhausted"
    assert result.confidence == 0.95
