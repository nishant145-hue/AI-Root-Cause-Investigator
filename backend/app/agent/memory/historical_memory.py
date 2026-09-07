from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from app.embeddings.huggingface_embeddings import embed_text
from app.vectorstore.qdrant_client import QdrantVectorStore


class HistoricalMemoryService:
    """
    Persists completed investigations into semantic vector memory.

    PostgreSQL remains the source of truth.
    Qdrant is used for semantic retrieval.
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
    ) -> None:

        self.vector_store = (
            vector_store
            or QdrantVectorStore()
        )

    @staticmethod
    def build_memory_text(
        investigation: dict[str, Any],
    ) -> str:
        """
        Convert an investigation into a semantic
        document suitable for embedding.
        """

        summary = investigation.get(
            "summary",
            "",
        )

        root_cause = investigation.get(
            "root_cause",
            "",
        )

        failed_component = investigation.get(
            "failed_component",
            "",
        )

        severity = investigation.get(
            "severity",
            "",
        )

        additional_notes = investigation.get(
            "additional_notes",
            "",
        )

        evidence = investigation.get(
            "evidence",
            [],
        )

        recommendations = investigation.get(
            "recommendations",
            [],
        )

        evidence_text = "\n".join(
            str(item)
            for item in evidence
        )

        recommendations_text = "\n".join(
            str(item)
            for item in recommendations
        )

        return (
            f"Incident Summary:\n"
            f"{summary}\n\n"
            f"Root Cause:\n"
            f"{root_cause}\n\n"
            f"Failed Component:\n"
            f"{failed_component}\n\n"
            f"Severity:\n"
            f"{severity}\n\n"
            f"Evidence:\n"
            f"{evidence_text}\n\n"
            f"Recommendations:\n"
            f"{recommendations_text}\n\n"
            f"Additional Notes:\n"
            f"{additional_notes}"
        ).strip()

    def store_investigation(
        self,
        investigation: dict[str, Any],
    ) -> None:
        """
        Store a completed investigation
        in Qdrant semantic memory.
        """

        investigation_id = investigation.get(
            "investigation_id"
        )

        if investigation_id is None:
            raise ValueError(
                "investigation_id is required."
            )

        memory_text = self.build_memory_text(
            investigation
        )

        if not memory_text:
            raise ValueError(
                "Cannot store empty investigation memory."
            )

        vector = embed_text(memory_text)

        payload = {
            "investigation_id": investigation_id,
            "user_id": investigation.get(
                "user_id"
            ),
            "summary": investigation.get(
                "summary",
                "",
            ),
            "root_cause": investigation.get(
                "root_cause",
                "",
            ),
            "failed_component": investigation.get(
                "failed_component",
                "",
            ),
            "severity": investigation.get(
                "severity",
                "",
            ),
            "confidence": investigation.get(
                "confidence"
            ),
            "additional_notes": investigation.get(
                "additional_notes",
                "",
            ),
        }

        self.vector_store.upsert(
            investigation_id=investigation_id,
            vector=vector,
            payload=payload,
        )
