from unittest.mock import patch

from app.agent.nodes.investigator import investigator_node


def test_investigator_derives_failed_component_and_severity():
    state = {
        "log_file_id": 303,
        "next_action": {
            "tool": "search_logs",
            "reason": "Investigate errors.",
            "parameters": {
                "severity": "ERROR",
                "limit": 50,
            },
        },
        "investigation_attempts": 0,
        "observations": [],
        "tool_calls": [],
        "tool_results": [],
        "execution_timeline": [],
        "failed_component": None,
        "severity": None,
    }

    logs = [
        {
            "id": "1",
            "severity": "ERROR",
            "component": "database",
            "message": "Connection pool exhausted",
            "raw_line": "ERROR database Connection pool exhausted",
        },
        {
            "id": "2",
            "severity": "CRITICAL",
            "component": "database",
            "message": "Database unavailable",
            "raw_line": "CRITICAL database Database unavailable",
        },
    ]

    with patch(
        "app.agent.nodes.investigator.search_logs",
        return_value=logs,
    ), patch(
        "app.agent.nodes.investigator.extract_evidence",
        return_value=[
            {
                "log_line": logs[0]["raw_line"],
                "reason": "ERROR log from component 'database'.",
            },
            {
                "log_line": logs[1]["raw_line"],
                "reason": "CRITICAL log from component 'database'.",
            },
        ],
    ):
        result = investigator_node(
            state,
            session=None,
        )

    assert result["failed_component"] == "database"
    assert result["severity"] == "CRITICAL"
    assert result["investigation_attempts"] == 1
