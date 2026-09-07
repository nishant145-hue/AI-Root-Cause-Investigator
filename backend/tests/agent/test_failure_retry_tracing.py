from unittest.mock import Mock, patch

from app.agent.agents.investigator import (
    InvestigatorAgent,
)
from app.agent.agents.memory import (
    MemoryAgent,
)


def test_failed_execution_records_attempt():

    agent = InvestigatorAgent()

    session = Mock()

    with patch(
        "app.agent.agents.investigator.search_logs",
        side_effect=RuntimeError(
            "database timeout"
        ),
    ):

        try:
            agent.search_logs(
                session=session,
                log_file_id=1,
                attempt=1,
            )
        except RuntimeError:
            pass

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["agent"] == "investigator"

    assert trace["status"] == "FAILED"

    assert trace["attempt"] == 1

    assert trace["error"] == (
        "database timeout"
    )


def test_retry_execution_records_second_attempt():

    agent = InvestigatorAgent()

    session = Mock()

    with patch(
        "app.agent.agents.investigator.search_logs",
        side_effect=[
            RuntimeError("temporary failure"),
            [
                {"id": 1},
                {"id": 2},
            ],
        ],
    ):

        try:
            agent.search_logs(
                session=session,
                log_file_id=1,
                attempt=1,
            )
        except RuntimeError:
            pass

        result = agent.search_logs(
            session=session,
            log_file_id=1,
            attempt=2,
        )

    assert len(result) == 2

    traces = agent.execution_traces()

    assert len(traces) == 2

    assert traces[0]["status"] == (
        "FAILED"
    )

    assert traces[0]["attempt"] == 1

    assert traces[1]["status"] == (
        "COMPLETED"
    )

    assert traces[1]["attempt"] == 2


def test_retry_summary_counts_attempts():

    agent = InvestigatorAgent()

    session = Mock()

    with patch(
        "app.agent.agents.investigator.search_logs",
        side_effect=[
            RuntimeError("timeout"),
            [{"id": 1}],
        ],
    ):

        try:
            agent.search_logs(
                session=session,
                log_file_id=1,
                attempt=1,
            )
        except RuntimeError:
            pass

        agent.search_logs(
            session=session,
            log_file_id=1,
            attempt=2,
        )

    summary = agent.execution_summary()

    assert summary[
        "total_executions"
    ] == 2

    assert summary[
        "completed_executions"
    ] == 1

    assert summary[
        "failed_executions"
    ] == 1

    assert summary[
        "retries"
    ] == 1


def test_memory_failure_records_retry_attempt():

    agent = MemoryAgent()

    with patch(
        "app.agent.agents.memory.InvestigationRetriever"
    ) as retriever_cls:

        retriever = (
            retriever_cls.return_value
        )

        retriever.search.side_effect = (
            RuntimeError(
                "Qdrant unavailable"
            )
        )

        try:
            agent.semantic_search(
                query="database timeout",
                user_id=10,
                attempt=2,
            )
        except RuntimeError:
            pass

    traces = agent.execution_traces()

    assert len(traces) == 1

    trace = traces[0]

    assert trace["status"] == "FAILED"

    assert trace["attempt"] == 2

    assert trace["error"] == (
        "Qdrant unavailable"
    )
