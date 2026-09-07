from __future__ import annotations

from typing import Any

from app.agent.agent_isolation import (
    get_isolated_agents,
    isolate_agent,
    record_reroute,
    select_reroute_agent,
)
from app.agent.agents.orchestrator import (
    MultiAgentOrchestrator,
)
from app.agent.failure import (
    AgentFailure,
    AgentFailureType,
    determine_recovery,
)
from app.agent.structured_logging import (
    agent_log_context,
    log_agent_event,
)


def failure_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Central failure-recovery node.

    Responsibilities:

    1. Identify the failed agent.
    2. Track failure attempts.
    3. Apply retry policy.
    4. Handle circuit-open failures.
    5. Isolate unhealthy agents.
    6. Reroute to a healthy agent.
    7. Stop safely when no recovery path exists.

    The node never executes another agent directly.
    It only produces routing state for LangGraph.
    """

    failed_agent = state.get("last_failed_agent")

    failure_type = state.get(
        "last_failure_type",
        "CRITICAL",
    )

    failure_message = state.get(
        "last_failure_message",
        "Unknown agent failure.",
    )

    # =========================================================
    # No failed agent
    # =========================================================

    if not failed_agent:
        return {
            "investigation_status": "FAILED",
            "recovery_action": "STOP",
            "next_agent": None,
            "failure_metadata": {
                "agent": None,
                "failure_type": "CRITICAL",
                "message": (
                    "Failure node was reached "
                    "without a failed agent."
                ),
                "terminal": True,
            },
        }

    # =========================================================
    # Retry counter
    # =========================================================

    retry_counts = dict(
        state.get(
            "retry_counts",
            {},
        )
    )

    attempt = (
        int(
            retry_counts.get(
                failed_agent,
                0,
            )
        )
        + 1
    )

    retry_counts[failed_agent] = attempt

    # =========================================================
    # Normalize failure type
    # =========================================================

    try:
        normalized_type = AgentFailureType(
            failure_type
        )
    except (
        ValueError,
        TypeError,
    ):
        normalized_type = AgentFailureType.CRITICAL

    # =========================================================
    # Controlled failure object
    # =========================================================

    failure = AgentFailure(
        agent=failed_agent,
        failure_type=normalized_type,
        message=failure_message,
        attempt=attempt,
    )

    # =========================================================
    # Recovery policy
    # =========================================================

    orchestrator = MultiAgentOrchestrator()

    max_retries = (
        orchestrator
        .retry_tracker
        .policy
        .max_retries
    )

    if failure_type == "CIRCUIT_OPEN":
        decision_action = "REROUTE"
        decision_reason = (
            "Agent circuit is open; "
            "execution must be rerouted."
        )
    else:
        decision = determine_recovery(
            failure,
            max_retries=max_retries,
        )

        decision_action = decision.action.value
        decision_reason = decision.reason

    # =========================================================
    # Failure history
    # =========================================================

    failures = list(
        state.get(
            "agent_failures",
            [],
        )
    )

    failure_record = {
        "agent": failed_agent,
        "failure_type": failure_type,
        "message": failure_message,
        "attempt": attempt,
        "recovery_action": decision_action,
        "recovery_reason": decision_reason,
    }

    failures.append(failure_record)

    # =========================================================
    # Existing isolation
    # =========================================================

    isolated_agents = list(
        get_isolated_agents(state)
    )

    update: dict[str, Any] = {
        "agent_failures": failures,
        "retry_counts": retry_counts,
        "last_failed_agent": failed_agent,
        "last_failure_type": failure_type,
        "last_failure_message": failure_message,
        "failure_metadata": {
            "agent": failed_agent,
            "failure_type": failure_type,
            "message": failure_message,
            "attempt": attempt,
            "recovery_action": decision_action,
            "recovery_reason": decision_reason,
        },
    }

    # =========================================================
    # RETRY
    # =========================================================

    if decision_action == "RETRY":

        # A retry is allowed only while the agent is not
        # isolated.

        if failed_agent in isolated_agents:

            update.update(
                {
                    "investigation_status": "FAILED",
                    "recovery_action": "STOP",
                    "next_agent": None,
                    "isolated_agents": isolated_agents,
                    "failure_metadata": {
                        **update[
                            "failure_metadata"
                        ],
                        "terminal": True,
                        "message": (
                            f"{failed_agent} is isolated; "
                            "retry is not allowed."
                        ),
                    },
                }
            )

            return update

        update.update(
            {
                "investigation_status": "RETRYING",
                "recovery_action": "RETRY",
                "next_agent": failed_agent,
                "isolated_agents": isolated_agents,
            }
        )

                # ---------------------------------------------------------
        # Structured retry event
        # ---------------------------------------------------------

        log_agent_event(
            "agent_execution_retry",
            level="INFO",
            agent_name=failed_agent,
            investigation_id=state.get(
                "investigation_id"
            ),
            attempt=attempt,
            execution_id=state.get(
                "execution_id"
            ),
            trace_id=state.get(
                "trace_id"
            ),
        )

        return update



    # =========================================================
    # REROUTE
    # =========================================================

    if decision_action == "REROUTE":

        # -----------------------------------------------------
        # Isolate failed agent.
        # -----------------------------------------------------

        isolate_agent(
            state,
            failed_agent,
        )

        isolated_agents = list(
            get_isolated_agents(state)
        )

        # -----------------------------------------------------
        # Prevent unlimited rerouting.
        # -----------------------------------------------------

        reroute_count = int(
            state.get(
                "reroute_count",
                0,
            )
        )


        if reroute_count >= 3:

            update.update(
                {
                    "investigation_status": "FAILED",
                    "recovery_action": "STOP",
                    "next_agent": None,
                    "isolated_agents": isolated_agents,
                    "failure_metadata": {
                        **update[
                            "failure_metadata"
                        ],
                        "terminal": True,
                        "reroute_count": reroute_count,
                        "message": (
                            "Maximum reroute limit reached."
                        ),
                    },
                }
            )

            return update

        # -----------------------------------------------------
        # Select healthy alternative.
        #
        # Failed agent is explicitly excluded.
        # -----------------------------------------------------

        target_agent = select_reroute_agent(
            state,
            failed_agent=failed_agent,
            candidates=[
                "reasoner",
                "validator",
                "planner",
            ],
        )

        # -----------------------------------------------------
        # No safe route.
        # -----------------------------------------------------

        if target_agent is None:

            update.update(
                {
                    "investigation_status": "FAILED",
                    "recovery_action": "STOP",
                    "next_agent": None,
                    "isolated_agents": list(
                        get_isolated_agents(state)
                    ),
                    "failure_metadata": {
                        **update[
                            "failure_metadata"
                        ],
                        "terminal": True,
                        "message": (
                            f"No safe recovery route "
                            f"available for {failed_agent}."
                        ),
                    },
                }
            )

            return update

        # -----------------------------------------------------
        # Record reroute.
        # -----------------------------------------------------

        record_reroute(
            state,
            failed_agent=failed_agent,
            target_agent=target_agent,
        )

        reroute_count = int(
            state.get(
                "reroute_count",
                0,
            )
        )

                # -----------------------------------------------------
        # Structured reroute event
        # -----------------------------------------------------

        log_agent_event(
            "agent_execution_rerouted",
            level="WARNING",
            agent_name=failed_agent,
            investigation_id=state.get(
                "investigation_id"
            ),
            target_agent=target_agent,
            reroute_count=reroute_count,
            execution_id=state.get(
                "execution_id"
            ),
            trace_id=state.get(
                "trace_id"
            ),
        )

        update.update(
            {
                "investigation_status": "REPLANNING",
                "recovery_action": "REROUTE",
                "next_agent": target_agent,
                "reroute_count": reroute_count,
                "last_rerouted_agent": failed_agent,
                "isolated_agents": list(
                    get_isolated_agents(state)
                ),
                "failure_metadata": {
                    **update[
                        "failure_metadata"
                    ],
                    "rerouted_to": target_agent,
                    "reroute_count": reroute_count,
                },
            }
        )

        return update

    # =========================================================
    # STOP
    # =========================================================

    update.update(
        {
            "investigation_status": "FAILED",
            "recovery_action": "STOP",
            "next_agent": None,
            "isolated_agents": isolated_agents,
            "failure_metadata": {
                **update[
                    "failure_metadata"
                ],
                "terminal": True,
            },
        }
    )

    return update
