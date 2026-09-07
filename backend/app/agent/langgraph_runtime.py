from __future__ import annotations

from typing import Any

from sqlmodel import Session

from app.agent.graph import build_investigation_graph
from app.agent.state import InvestigationState
from app.database.session import engine
from app.services.llm.schemas import (
    AIInvestigationResponse,
    Evidence,
    Recommendation,
)


class LangGraphInvestigationError(RuntimeError):
    """Raised when a LangGraph investigation cannot produce a valid result."""


def _build_initial_state(
    *,
    investigation_id: int,
    user_id: int,
    log_file_id: int,
    incident_summary: str,
    summary: str | None = None,
    severity: str | None = None,
    additional_notes: str | None = None,
    existing_failed_component: str | None = None,
    existing_severity: str | None = None,
) -> InvestigationState:
    """Build the initial state for a LangGraph investigation."""

    return {
        "investigation_id": investigation_id,
        "user_id": user_id,
        "log_file_id": log_file_id,
        "incident_summary": incident_summary,

        "plan": [],
        "current_step": "Starting investigation",
        "next_action": None,
        "next_agent": None,

        "observations": [],
        "evidence": [],
        "historical_incidents": [],
        "hypotheses": [],

        "tool_calls": [],
        "tool_results": [],
        "remaining_questions": [],

        "confidence": None,
        "root_cause": None,
        "failed_component": existing_failed_component,

        "investigation_attempts": 0,
        "investigation_status": "STARTING",

        "agent_failures": [],
        "retry_counts": {},

        "last_failed_agent": None,
        "last_failure_type": None,
        "last_failure_message": None,

        "recovery_action": None,
        "failure_metadata": {},

        "cancellation_requested": False,
        "cancellation_reason": None,
        "cancelled_agent": None,
        "cancellation_metadata": {},

        "circuit_breaker_states": {},
        "circuit_breaker_failures": {},
        "circuit_breaker_opened_at": {},

        "isolated_agents": [],
        "reroute_count": 0,
        "last_rerouted_agent": None,

        "execution_timeline": [],
        "execution_analytics": {},

        # Compatibility fields used by the final response adapter.
        "summary": incident_summary,
        "severity": existing_severity,
        "additional_notes": None,
    }


def _map_evidence(
    state: InvestigationState,
) -> list[Evidence]:
    """Convert graph evidence into the existing response schema."""

    result: list[Evidence] = []

    for item in state.get("evidence", []):
        if not isinstance(item, dict):
            continue

        log_line = item.get("log_line")
        reason = item.get("reason")

        if not log_line or not reason:
            continue

        result.append(
            Evidence(
                log_line=str(log_line),
                reason=str(reason),
            )
        )

    return result


def _map_recommendations(
    state: InvestigationState,
) -> list[Recommendation]:
    """
    Convert validated hypothesis information into the existing
    recommendation schema without inventing a remediation action.
    """

    recommendations: list[Recommendation] = []

    for hypothesis in state.get("hypotheses", []):
        if not isinstance(hypothesis, dict):
            continue

        if hypothesis.get("status") != "VALIDATED":
            continue

        cause = hypothesis.get("cause")

        if not cause:
            continue

        recommendations.append(
            Recommendation(
                title="Investigate validated root cause",
                description=(
                    "Investigate and remediate the validated "
                    f"root cause: {cause}"
                ),
            )
        )

        break

    return recommendations


def _map_final_state(
    state: InvestigationState,
) -> AIInvestigationResponse:
    """Convert the final graph state to the existing API contract."""

    status = state.get("investigation_status")

    if status != "ROOT_CAUSE_VALIDATED":
        raise LangGraphInvestigationError(
            "LangGraph investigation did not validate a root cause. "
            f"Final status: {status!r}"
        )

    root_cause = state.get("root_cause")

    if not root_cause:
        raise LangGraphInvestigationError(
            "LangGraph investigation completed without a root cause."
        )

    confidence = state.get("confidence")

    if confidence is None:
        raise LangGraphInvestigationError(
            "LangGraph investigation completed without confidence."
        )

    summary = state.get("summary")

    if not summary:
        summary = state.get(
            "incident_summary",
            "AI investigation completed.",
        )

    failed_component = state.get("failed_component")

    if not failed_component:
        raise LangGraphInvestigationError(
            "LangGraph investigation completed without a failed component."
        )

    severity = state.get("severity")

    if not severity:
        raise LangGraphInvestigationError(
            "LangGraph investigation completed without severity."
        )

    additional_notes = state.get(
        "additional_notes"
    )

    remaining_questions = state.get(
        "remaining_questions",
        [],
    )

    if remaining_questions:
        additional_notes = (
            (
                f"{additional_notes}\n"
                if additional_notes
                else ""
            )
            + "Remaining investigation questions: "
            + "; ".join(
                str(question)
                for question in remaining_questions
            )
        )

    return AIInvestigationResponse(
        summary=str(summary),
        root_cause=str(root_cause),
        failed_component=str(failed_component),
        severity=str(severity),
        confidence=float(confidence),
        evidence=_map_evidence(state),
        recommendations=_map_recommendations(state),
        additional_notes=additional_notes,
    )


def run_langgraph_investigation(
    *,
    investigation_id: int,
    user_id: int,
    log_file_id: int,
    incident_summary: str,
    existing_failed_component: str | None = None,
    existing_severity: str | None = None,
) -> tuple[
    AIInvestigationResponse,
    dict[str, Any],
]:
    """
    Execute LangGraph using a worker-owned database session.

    The function is intended to run through AgentExecutionManager.
    """

    initial_state = _build_initial_state(
        investigation_id=investigation_id,
        user_id=user_id,
        log_file_id=log_file_id,
        incident_summary=incident_summary,
        existing_failed_component=existing_failed_component,
        existing_severity=existing_severity,
    )

    with Session(engine) as session:
        graph = build_investigation_graph(session)

        try:
            final_state = graph.invoke(initial_state)
        except Exception as exc:
            raise LangGraphInvestigationError(
                "LangGraph investigation execution failed."
            ) from exc

    if not isinstance(final_state, dict):
        raise LangGraphInvestigationError(
            "LangGraph returned an invalid final state."
        )

    result = _map_final_state(final_state)

    execution_analytics = final_state.get(
        "execution_analytics",
        {},
    )

    return result, execution_analytics
