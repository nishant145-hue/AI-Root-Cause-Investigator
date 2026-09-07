from app.agent.state import InvestigationAction, InvestigationState


def planner_node(
    state: InvestigationState,
) -> dict:
    """
    Dynamically select the next investigation action
    based on the current investigation state.
    """

    evidence = state.get("evidence", [])
    hypotheses = state.get("hypotheses", [])
    attempts = state.get("investigation_attempts", 0)

    plan = list(state.get("plan", []))

    # ---------------------------------------------------------
    # First investigation cycle
    # ---------------------------------------------------------

    if attempts == 0:
        action: InvestigationAction = {
            "tool": "search_logs",
            "reason": (
                "Start by identifying error logs associated "
                "with the incident."
            ),
            "parameters": {
                "severity": "ERROR",
                "limit": 50,
            },
        }

        plan.append(
            "Search error logs for initial evidence."
        )

        return {
            "plan": plan,
            "next_action": action,
            "current_step": "Execute initial log investigation",
            "investigation_status": "PLANNING",
        }

    # ---------------------------------------------------------
    # If database evidence exists
    # ---------------------------------------------------------

    database_evidence = [
        item
        for item in evidence
        if any(
            keyword in item["log_line"].lower()
            for keyword in (
                "database",
                "connection",
                "timeout",
            )
        )
    ]

    if database_evidence and attempts == 1:
        action = {
            "tool": "search_logs",
            "reason": (
                "Database-related evidence was found. "
                "Investigate database errors in more detail."
            ),
            "parameters": {
                "query": "database",
                "severity": "ERROR",
                "limit": 50,
            },
        }

        plan.append(
            "Investigate database-related errors."
        )

        return {
            "plan": plan,
            "next_action": action,
            "current_step": (
                "Investigate database-related evidence"
            ),
            "investigation_status": "PLANNING",
        }

    # ---------------------------------------------------------
    # If a strong hypothesis exists
    # ---------------------------------------------------------

    if hypotheses:
        strongest = max(
            hypotheses,
            key=lambda hypothesis: hypothesis["confidence"],
        )

        action = {
            "tool": "search_logs",
            "reason": (
                "Collect additional evidence related "
                "to the strongest hypothesis."
            ),
            "parameters": {
                "query": strongest["cause"],
                "severity": "ERROR",
                "limit": 50,
            },
        }

        plan.append(
            "Collect additional evidence for the "
            f"'{strongest['cause']}' hypothesis."
        )

        return {
            "plan": plan,
            "next_action": action,
            "current_step": (
                "Investigate strongest hypothesis"
            ),
            "investigation_status": "PLANNING",
        }

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------

    action = {
        "tool": "search_logs",
        "reason": (
            "No specific investigation direction has "
            "been identified. Search additional errors."
        ),
        "parameters": {
            "severity": "ERROR",
            "limit": 50,
        },
    }

    plan.append(
        "Search additional error logs."
    )

    return {
        "plan": plan,
        "next_action": action,
        "current_step": "Search additional evidence",
        "investigation_status": "PLANNING",
    }
