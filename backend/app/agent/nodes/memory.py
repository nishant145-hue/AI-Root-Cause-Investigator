from sqlmodel import Session

from app.agent.memory.historical import (
    search_historical_incidents,
)
from app.agent.state import InvestigationState
from app.agent.state_timeline import (
    propagate_timeline,
)
from app.vectorstore.retriever import (
    InvestigationRetriever,
)


def memory_node(
    state: InvestigationState,
    session: Session,
) -> dict:
    """
    Retrieve historical investigation context.

    Combines:
    1. PostgreSQL historical memory.
    2. Qdrant semantic memory.

    Both sources are isolated by user_id.
    """

    investigation_id = state[
        "investigation_id"
    ]

    user_id = state["user_id"]

    incident_summary = state[
        "incident_summary"
    ]

    # ---------------------------------------------------------
    # PostgreSQL historical memory
    # ---------------------------------------------------------

    historical_incidents = (
        search_historical_incidents(
            session=session,
            current_investigation_id=(
                investigation_id
            ),
            user_id=user_id,
            incident_summary=incident_summary,
            limit=5,
        )
    )

    # ---------------------------------------------------------
    # Qdrant semantic memory
    # ---------------------------------------------------------

    retriever = InvestigationRetriever()

    semantic_incidents = retriever.search(
        query=incident_summary,
        limit=5,
        user_id=user_id,
    )

    # ---------------------------------------------------------
    # Merge both memory sources
    # ---------------------------------------------------------

    combined = []

    seen_ids = set()

    for incident in (
        historical_incidents
        + semantic_incidents
    ):

        incident_id = incident.get(
            "investigation_id"
        )

        if incident_id is None:
            continue

        # -----------------------------------------------------
        # Security check
        # -----------------------------------------------------

        incident_user_id = incident.get(
            "user_id"
        )

        if (
            incident_user_id is not None
            and incident_user_id != user_id
        ):
            continue

        # -----------------------------------------------------
        # Remove duplicate investigations
        # -----------------------------------------------------

        if incident_id in seen_ids:
            continue

        seen_ids.add(incident_id)

        combined.append(incident)

        # ---------------------------------------------------------
    # Execution timeline
    # ---------------------------------------------------------

    timeline_entry = {
        "agent": "memory",
        "action": "retrieve_historical_memory",
        "status": "COMPLETED",
        "historical_count": len(
            historical_incidents
        ),
        "semantic_count": len(
            semantic_incidents
        ),
        "combined_count": len(combined),
    }

    updated_timeline = propagate_timeline(
        state,
        [timeline_entry],
    )["execution_timeline"]

    return {
        "historical_incidents": combined,
        "execution_timeline": updated_timeline,
    }
