from sqlmodel import Session

from app.agent.state import InvestigationState
from app.agent.state_timeline import (
    propagate_timeline,
)
from app.agent.tools.evidence import extract_evidence
from app.agent.tools.logs import search_logs


def investigator_node(
    state: InvestigationState,
    session: Session,
) -> dict:
    """
    Execute the investigation action selected by the planner.

    The investigator:
    - searches application logs
    - extracts evidence
    - records tool calls
    - records tool results
    - tracks investigation attempts
    - appends execution information to the unified timeline
    """

    log_file_id = state["log_file_id"]

    attempts = (
        state.get(
            "investigation_attempts",
            0,
        )
        + 1
    )

    action = state.get("next_action")

    if action is None:
        action = {
            "tool": "search_logs",
            "reason": "Initial log investigation.",
            "parameters": {
                "severity": "ERROR",
                "limit": 50,
            },
        }

    parameters = action.get(
        "parameters",
        {},
    )

    # ---------------------------------------------------------
    # Search logs
    # ---------------------------------------------------------

    logs = search_logs(
        session=session,
        log_file_id=log_file_id,
        query=parameters.get("query"),
        severity=parameters.get("severity"),
        component=parameters.get("component"),
        limit=parameters.get(
            "limit",
            50,
        ),
    )

        # ---------------------------------------------------------
    # Investigation metadata
    # ---------------------------------------------------------

    failed_component = state.get(
        "failed_component"
    )

    severity = state.get(
        "severity"
    )

    severity_priority = {
        "CRITICAL": 4,
        "ERROR": 3,
        "WARNING": 2,
        "INFO": 1,
    }

    for log in logs:
        log_severity = str(
            log.get("severity", "")
        ).upper()

        component = str(
            log.get("component", "")
        ).strip()

        if (
            component
            and log_severity in {"ERROR", "CRITICAL"}
        ):
            if failed_component is None:
                failed_component = component

        if log_severity in severity_priority:
            if (
                severity is None
                or severity_priority[log_severity]
                > severity_priority.get(
                    str(severity).upper(),
                    0,
                )
            ):
                severity = log_severity
    # ---------------------------------------------------------
    # Extract evidence
    # ---------------------------------------------------------

    evidence = extract_evidence(
        logs
    )

    # ---------------------------------------------------------
    # Observations
    # ---------------------------------------------------------

    observations = list(
        state.get(
            "observations",
            [],
        )
    )

    observations.append(
        {
            "type": "tool_execution",
            "tool": action["tool"],
            "reason": action["reason"],
            "message": (
                f"Investigation attempt {attempts} "
                f"executed {action['tool']} and found "
                f"{len(logs)} matching logs."
            ),
        }
    )

    # ---------------------------------------------------------
    # Tool calls
    # ---------------------------------------------------------

    tool_calls = list(
        state.get(
            "tool_calls",
            [],
        )
    )

    tool_calls.append(
        {
            "tool": action["tool"],
            "arguments": {
                "log_file_id": log_file_id,
                **parameters,
            },
            "reason": action["reason"],
            "attempt": attempts,
            "result_count": len(logs),
        }
    )

    # ---------------------------------------------------------
    # Tool results
    # ---------------------------------------------------------

    tool_results = list(
        state.get(
            "tool_results",
            [],
        )
    )

    tool_results.append(
        {
            "tool": action["tool"],
            "result_count": len(logs),
            "attempt": attempts,
        }
    )

    # ---------------------------------------------------------
    # Execution timeline
    # ---------------------------------------------------------

    timeline_entry = {
        "agent": "investigator",
        "action": action["tool"],
        "status": "COMPLETED",
        "attempt": attempts,
        "result_count": len(logs),
    }

    updated_timeline = propagate_timeline(
        state,
        [timeline_entry],
    )["execution_timeline"]

    # ---------------------------------------------------------
    # Return updated LangGraph state
    # ---------------------------------------------------------

    return {
        "observations": observations,
        "evidence": evidence,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "investigation_attempts": attempts,
        "failed_component": failed_component,
        "severity": severity,
        "current_step": (
            "Evaluate collected evidence"
        ),
        "investigation_status": (
            "INVESTIGATING"
        ),
        "execution_timeline": (
            updated_timeline
        ),
    }
