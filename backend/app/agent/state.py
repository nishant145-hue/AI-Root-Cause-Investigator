from typing import TypedDict

class Hypothesis(TypedDict):
    """
    A possible explanation for the incident.
    """

    cause: str
    confidence: float
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    status: str

class InvestigationAction(TypedDict):
    """
    Represents the next action selected by the agent.
    """

    tool: str
    reason: str
    parameters: dict


class HistoricalIncident(TypedDict):
    investigation_id: int
    similarity: float
    summary: str
    root_cause: str
    failed_component: str
    severity: str
    confidence: float | None

from typing import Any, TypedDict


class InvestigationState(TypedDict, total=False):

    # Identity
    investigation_id: int
    user_id: int
    log_file_id: int

    # Incident
    incident_summary: str

    # Planning
    plan: list
    current_step: str
    next_action: str | None
    next_agent: str | None

    # Investigation
    observations: list
    evidence: list

    # Historical memory
    historical_incidents: list

    # Reasoning
    hypotheses: list

    # Tool execution
    tool_calls: list
    tool_results: list

    # Reflection
    remaining_questions: list

    # Final result
    confidence: float | None
    root_cause: str | None
    failed_component: str | None

    # Workflow
    investigation_attempts: int
    investigation_status: str

    agent_failures: list[dict]
    retry_counts: dict[str, int]

    last_failed_agent: str | None
    last_failure_type: str | None
    last_failure_message: str | None

    recovery_action: str | None

    failure_metadata: dict[str, Any]

    # Cancellation
    cancellation_requested: bool
    cancellation_reason: str | None
    cancelled_agent: str | None
    cancellation_metadata: dict[str, Any]

    circuit_breaker_states: dict[str, str]
    circuit_breaker_failures: dict[str, int]
    circuit_breaker_opened_at: dict[str, float]
    _circuit_breaker: Any

    isolated_agents: list[str]
    reroute_count: int
    last_rerouted_agent: str | None

    execution_timeline: list[dict[str, Any]]
    execution_analytics: dict[str, Any]
