from datetime import datetime
from uuid import uuid4

from app.agent.tools.logs import search_logs


class FakeLog:
    def __init__(
        self,
        severity: str,
        component: str,
        message: str,
        source: str = "application",
    ):
        self.id = uuid4()
        self.timestamp = datetime.utcnow()
        self.severity = severity
        self.source = source
        self.component = component
        self.message = message
        self.raw_line = message


def test_search_logs_filters_results(monkeypatch):

    logs = [
        FakeLog(
            severity="ERROR",
            component="database",
            message="Database connection timeout",
        ),
        FakeLog(
            severity="INFO",
            component="payment-api",
            message="Payment request completed",
        ),
        FakeLog(
            severity="ERROR",
            component="payment-api",
            message="Payment service timeout",
        ),
    ]

    def fake_get_logs(session, log_file_id):
        return logs

    monkeypatch.setattr(
        "app.agent.tools.logs.ParsedLogService.get_logs",
        fake_get_logs,
    )

    results = search_logs(
        session=None,
        log_file_id=1,
        query="timeout",
    )

    assert len(results) == 2
    assert all(
        "timeout" in result["message"].lower()
        for result in results
    )
