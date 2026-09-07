from __future__ import annotations

from typing import Any

from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from sqlmodel import Session

from app.agent.agent_isolation import (
    is_agent_isolated,
)
from app.agent.nodes.analytics import (
    analytics_node,
)
from app.agent.nodes.failure import (
    failure_node,
)
from app.agent.nodes.investigator import (
    investigator_node,
)
from app.agent.nodes.memory import (
    memory_node,
)
from app.agent.nodes.memory_writer import (
    memory_writer_node,
)
from app.agent.nodes.orchestrator import (
    orchestrator_node,
)
from app.agent.nodes.planner import (
    planner_node,
)
from app.agent.nodes.reasoner import (
    reasoner_node,
)
from app.agent.nodes.reflector import (
    reflector_node,
)
from app.agent.nodes.validator import (
    validator_node,
)
from app.agent.recovery import (
    run_with_failure_capture,
)
from app.agent.state import (
    InvestigationState,
)

MAX_INVESTIGATION_ATTEMPTS = 3
MAX_REROUTES = 3


# =============================================================
# Reflection routing
# =============================================================

def route_after_reflection(
    state: InvestigationState,
) -> str:

    status = state.get(
        "investigation_status"
    )

    if status == "READY_FOR_VALIDATION":
        return "validator"

    if status == "FAILED":
        return "validator"

    attempts = int(
        state.get(
            "investigation_attempts",
            0,
        )
    )

    if attempts >= MAX_INVESTIGATION_ATTEMPTS:
        return "validator"

    return "planner"


# =============================================================
# Failure routing
# =============================================================

def route_after_failure(
    state: InvestigationState,
) -> str:
    """
    Route the failure node.

    STOP always terminates the graph.

    RETRY executes only the requested non-isolated agent.

    REROUTE executes only the selected healthy agent.
    """

    action = state.get(
        "recovery_action"
    )

    # ---------------------------------------------------------
    # TERMINAL FAILURE
    # ---------------------------------------------------------

    if action == "STOP":
        return "end"

    # ---------------------------------------------------------
    # Maximum reroutes
    # ---------------------------------------------------------

    reroute_count = int(
        state.get(
            "reroute_count",
            0,
        )
    )

    if reroute_count >= MAX_REROUTES:
        return "end"

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------

    if action == "RETRY":

        next_agent = state.get(
            "next_agent"
        )

        if not next_agent:
            return "end"

        if is_agent_isolated(
            state,
            next_agent,
        ):
            return "end"

        if next_agent == "investigator":
            return "investigator"

        if next_agent == "reasoner":
            return "reasoner"

        if next_agent == "validator":
            return "validator"

        if next_agent == "planner":
            return "planner"

        return "end"

    # ---------------------------------------------------------
    # REROUTE
    # ---------------------------------------------------------

    if action == "REROUTE":

        next_agent = state.get(
            "next_agent"
        )

        if not next_agent:
            return "end"

        if is_agent_isolated(
            state,
            next_agent,
        ):
            return "end"

        if next_agent == "investigator":
            return "investigator"

        if next_agent == "reasoner":
            return "reasoner"

        if next_agent == "validator":
            return "validator"

        if next_agent == "planner":
            return "planner"

        return "end"

    # ---------------------------------------------------------
    # Unknown action
    # ---------------------------------------------------------

    return "end"


# =============================================================
# Generic agent routing
# =============================================================

def route_after_agent(
    state: InvestigationState,
    success_target: str,
) -> str:

    failed_agent = state.get(
        "last_failed_agent"
    )

    if failed_agent:
        return "failure"

    return success_target


# =============================================================
# Safe investigator execution
# =============================================================

def safe_investigator_node(
    state: InvestigationState,
    session: Session,
) -> dict[str, Any]:
    """
    Execute the investigator through the centralized
    production failure-recovery layer.
    """

    result = run_with_failure_capture(
        state=state,
        agent_name="investigator",
        node=investigator_node,
        session=session,
    )

    return _merge_reliability_state(
        state,
        result,
    )

def _merge_reliability_state(
    state: InvestigationState,
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Preserve reliability state while clearing stale failure
    routing information after successful agent execution.
    """

    merged = dict(result)

    reliability_fields = (
        "circuit_breaker_states",
        "circuit_breaker_failures",
        "circuit_breaker_opened_at",
        "isolated_agents",
        "reroute_count",
        "last_rerouted_agent",
    )

    for field in reliability_fields:
        if field in state:
            merged[field] = state[field]

    # ---------------------------------------------------------
    # Successful execution
    # ---------------------------------------------------------
    #
    # run_with_failure_capture() returns last_failed_agent
    # when execution fails. A successful execution does not.
    #
    # Clear stale failure-routing state so route_after_agent()
    # does not send a successful retry back to failure.
    #
    if "last_failed_agent" not in result:
        merged["last_failed_agent"] = None
        merged["last_failure_type"] = None
        merged["last_failure_message"] = None
        merged["recovery_action"] = None

    return merged


def safe_planner_node(
    state: InvestigationState,
) -> dict[str, Any]:

    result = run_with_failure_capture(
        state=state,
        agent_name="planner",
        node=planner_node,
    )

    return _merge_reliability_state(
        state,
        result,
    )

def safe_orchestrator_node(
    state: InvestigationState,
) -> dict[str, Any]:

    result = run_with_failure_capture(
        state=state,
        agent_name="orchestrator",
        node=orchestrator_node,
    )

    return _merge_reliability_state(
        state,
        result,
    )


def safe_reasoner_node(
    state: InvestigationState,
) -> dict[str, Any]:

    result = run_with_failure_capture(
        state=state,
        agent_name="reasoner",
        node=reasoner_node,
    )

    return _merge_reliability_state(
        state,
        result,
    )


def safe_validator_node(
    state: InvestigationState,
) -> dict[str, Any]:

    result = run_with_failure_capture(
        state=state,
        agent_name="validator",
        node=validator_node,
    )

    return _merge_reliability_state(
        state,
        result,
    )
# =============================================================
# Orchestrator routing
# =============================================================

def route_after_orchestrator(
    state: InvestigationState,
) -> str:
    """
    Route according to the orchestrator decision.

    An isolated agent must never be selected again.
    If the orchestrator selects an isolated agent, use
    a safe fallback instead of returning to planner forever.
    """

    next_agent = state.get("next_agent")

    # Completed investigation
    if next_agent == "completed":
        return "memory_writer"

    # No decision
    if not next_agent:
        return "investigator"

    # ---------------------------------------------------------
    # Never execute an isolated agent
    # ---------------------------------------------------------

    if next_agent in {
        "investigator",
        "reasoner",
        "validator",
        "memory",
    } and is_agent_isolated(
        state,
        next_agent,
    ):
        # Investigator is isolated. Do NOT go back to
        # planner because planner -> orchestrator could
        # select investigator again.
        #
        # Prefer validator as the terminal-safe route.
        if not is_agent_isolated(
            state,
            "validator",
        ):
            return "validator"

        # If validator is also isolated, finish safely.
        return "memory_writer"

    # ---------------------------------------------------------
    # Normal routing
    # ---------------------------------------------------------

    if next_agent == "investigator":
        return "investigator"

    if next_agent == "memory":
        return "memory"

    if next_agent == "reasoner":
        return "reasoner"

    if next_agent == "validator":
        return "validator"

    if next_agent == "planner":
        return "planner"

    return "investigator"

# =============================================================
# Build graph
# =============================================================

def build_investigation_graph(
    session: Session,
):

    graph = StateGraph(
        InvestigationState
    )

    # =========================================================
    # Nodes
    # =========================================================

    graph.add_node(
        "planner",
        safe_planner_node,
    )

    graph.add_node(
        "orchestrator",
        safe_orchestrator_node,
    )

    graph.add_node(
        "memory",
        lambda state: memory_node(
            state,
            session,
        ),
    )

    graph.add_node(
        "investigator",
        lambda state: safe_investigator_node(
            state,
            session,
        ),
    )

    graph.add_node(
        "reasoner",
        safe_reasoner_node,
    )

    graph.add_node(
        "reflector",
        reflector_node,
    )

    graph.add_node(
        "validator",
        safe_validator_node,
    )

    graph.add_node(
        "memory_writer",
        memory_writer_node,
    )

    graph.add_node(
        "analytics",
        analytics_node,
    )

    graph.add_node(
        "failure",
        failure_node,
    )

    # =========================================================
    # START
    # =========================================================

    graph.add_edge(
        START,
        "memory",
    )

    # =========================================================
    # MEMORY
    # =========================================================

    graph.add_edge(
        "memory",
        "planner",
    )

    # =========================================================
    # PLANNER
    # =========================================================

    graph.add_edge(
        "planner",
        "orchestrator",
    )

    # =========================================================
    # ORCHESTRATOR
    # =========================================================

    graph.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "investigator": "investigator",
            "memory": "memory",
            "reasoner": "reasoner",
            "validator": "validator",
            "planner": "planner",
            "memory_writer": "memory_writer",
        },
    )

    # =========================================================
    # INVESTIGATOR
    # =========================================================

    graph.add_conditional_edges(
        "investigator",
        lambda state: route_after_agent(
            state,
            "reasoner",
        ),
        {
            "failure": "failure",
            "reasoner": "reasoner",
        },
    )

    # =========================================================
    # REASONER
    # =========================================================

    graph.add_edge(
        "reasoner",
        "reflector",
    )

    # =========================================================
    # REFLECTOR
    # =========================================================

    graph.add_conditional_edges(
        "reflector",
        route_after_reflection,
        {
            "planner": "planner",
            "validator": "validator",
        },
    )

    # =========================================================
    # VALIDATOR
    # =========================================================

    graph.add_conditional_edges(
        "validator",
        lambda state: route_after_agent(
            state,
            "memory_writer",
        ),
        {
            "failure": "failure",
            "memory_writer": "memory_writer",
        },
    )

    # =========================================================
    # FAILURE
    # =========================================================

    graph.add_conditional_edges(
        "failure",
        route_after_failure,
        {
            "investigator": "investigator",
            "reasoner": "reasoner",
            "validator": "validator",
            "planner": "planner",
            "end": END,
        },
    )

    # =========================================================
    # COMPLETION
    # =========================================================

    graph.add_edge(
        "memory_writer",
        "analytics",
    )

    graph.add_edge(
        "analytics",
        END,
    )

    return graph.compile()
