from app.agent.memory.quality import (
    calculate_memory_quality,
    classify_memory_quality,
)

from app.embeddings.huggingface_embeddings import (
    embed_text,
)

from app.vectorstore.qdrant_client import (
    QdrantVectorStore,
)


MIN_MEMORY_QUALITY = 0.60


class InvestigationRetriever:
    """
    Semantic retriever for historical investigations.

    Retrieval considers both:

    1. Semantic similarity.
    2. Historical memory quality.
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
    ) -> None:

        self.vector_store = (
            vector_store
            or QdrantVectorStore()
        )

    def search(
        self,
        query: str,
        limit: int = 5,
        user_id: int | None = None,
    ) -> list[dict]:

        if not query or not query.strip():
            return []

        vector = embed_text(query)

        results = self.vector_store.search(
            vector=vector,
            limit=limit,
            user_id=user_id,
        )

        historical_incidents = []

        for result in results:

            payload = result.payload or {}

            similarity = float(
                result.score
            )

            confidence = float(
                payload.get(
                    "confidence",
                    0.0,
                )
                or 0.0
            )

            age_days = float(
                payload.get(
                    "age_days",
                    0.0,
                )
                or 0.0
            )

            validated = bool(
                payload.get(
                    "validated",
                    True,
                )
            )

            evidence_count = int(
                payload.get(
                    "evidence_count",
                    1,
                )
                or 0
            )

            # -------------------------------------------------
            # Calculate memory quality
            # -------------------------------------------------

            memory_quality = (
                calculate_memory_quality(
                    similarity=similarity,
                    confidence=confidence,
                    age_days=age_days,
                    validated=validated,
                    evidence_count=evidence_count,
                )
            )

            memory_status = (
                classify_memory_quality(
                    memory_quality
                )
            )

            # -------------------------------------------------
            # Ignore stale / unreliable memories
            # -------------------------------------------------

            # ---------------------------------------------------------
            # Ignore stale historical memories
            # ---------------------------------------------------------

            if memory_quality < MIN_MEMORY_QUALITY:
                continue

            # -------------------------------------------------
            # Confidence-aware ranking
            # -------------------------------------------------

            ranking_score = (
                similarity * 0.60
                + memory_quality * 0.40
            )

            historical_incidents.append(
                {
                    "investigation_id": (
                        payload.get(
                            "investigation_id"
                        )
                    ),

                    "similarity": similarity,

                    "memory_quality": (
                        memory_quality
                    ),

                    "memory_status": (
                        memory_status
                    ),

                    "ranking_score": round(
                        ranking_score,
                        4,
                    ),

                    "summary": payload.get(
                        "summary",
                        "",
                    ),

                    "root_cause": payload.get(
                        "root_cause",
                        "",
                    ),

                    "failed_component": (
                        payload.get(
                            "failed_component",
                            "",
                        )
                    ),

                    "severity": payload.get(
                        "severity",
                        "",
                    ),

                    "confidence": confidence,

                    "user_id": payload.get(
                        "user_id"
                    ),
                }
            )

        # -----------------------------------------------------
        # Highest confidence-aware ranking first
        # -----------------------------------------------------

        historical_incidents.sort(
            key=lambda item: item[
                "ranking_score"
            ],
            reverse=True,
        )

        return historical_incidents[:limit]
