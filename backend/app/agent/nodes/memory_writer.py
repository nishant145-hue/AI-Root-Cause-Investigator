from typing import Any

from app.agent.state import InvestigationState
from app.embeddings.huggingface_embeddings import embed_text
from app.vectorstore.qdrant_client import QdrantVectorStore


def memory_writer_node(
    state: InvestigationState,
) -> dict[str, Any]:

    if state.get("memory_stored"):
        return {}

    if state.get("investigation_status") != (
        "ROOT_CAUSE_VALIDATED"
    ):
        return {}

    investigation_id = state.get(
        "investigation_id"
    )

    user_id = state.get(
        "user_id"
    )

    incident_summary = state.get(
        "incident_summary",
        "",
    )

    root_cause = state.get(
        "root_cause"
    )

    failed_component = state.get(
        "failed_component"
    )

    confidence = state.get(
        "confidence"
    )

    # ---------------------------------------------------------
    # Safety validation
    # ---------------------------------------------------------

    if not investigation_id:
        return {}

    if not user_id:
        return {}

    if not root_cause:
        return {}

    # ---------------------------------------------------------
    # Build semantic memory text
    # ---------------------------------------------------------

    memory_text = (
        f"Incident: {incident_summary}\n"
        f"Root cause: {root_cause}\n"
        f"Failed component: "
        f"{failed_component or 'unknown'}"
    )

    # ---------------------------------------------------------
    # Generate embedding
    # ---------------------------------------------------------

    vector = embed_text(
        memory_text
    )

    # ---------------------------------------------------------
    # Store in Qdrant
    # ---------------------------------------------------------

    vector_store = QdrantVectorStore()

    vector_store.ensure_collection()

    payload = {
        "investigation_id": investigation_id,
        "user_id": user_id,
        "summary": incident_summary,
        "root_cause": root_cause,
        "failed_component": failed_component,
        "severity": state.get("severity"),
        "confidence": confidence,
    }

    vector_store.upsert(
        investigation_id=investigation_id,
        vector=vector,
        payload=payload,
    )

    return {
        "memory_stored": True,
    }
