from typing import Any

from app.agent.agents.base import BaseAgent
from app.agent.memory.historical import (
    search_historical_incidents,
)
from app.vectorstore.retriever import (
    InvestigationRetriever,
)


class MemoryAgent(BaseAgent):
    """
    Specialized agent responsible for retrieving
    historical investigation memory.

    MemoryAgent owns:
    - PostgreSQL historical search
    - Qdrant semantic search

    Memory retrieval is always isolated by user_id.
    """

    name = "memory"

    role = (
        "Retrieve relevant historical investigations "
        "and semantic memory for the current incident."
    )

    def __init__(self) -> None:
        super().__init__(
            capabilities=[
                "search_historical_incidents",
                "semantic_memory_search",
            ]
        )

    def search_historical_incidents(
        self,
        session: Any,
        current_investigation_id: int,
        user_id: int,
        incident_summary: str,
        limit: int = 5,
        attempt: int = 1
    ) -> list[dict]:

        self.require_capability(
            "search_historical_incidents"
        )

        trace = self.start_trace(
            action="search_historical_incidents",
            attempt=attempt,
            metadata={
                "investigation_id": (
                    current_investigation_id
                ),
                "user_id": user_id,
                "limit": limit,
            },
        )

        try:
            results = search_historical_incidents(
                session=session,
                current_investigation_id=(
                    current_investigation_id
                ),
                user_id=user_id,
                incident_summary=incident_summary,
                limit=limit,
            )

            trace.metadata[
                "result_count"
            ] = len(results)

            trace.complete()

            return results

        except Exception as exc:

            trace.complete(
                status="FAILED",
                error=str(exc),
            )

            raise

    def semantic_search(
        self,
        query: str,
        user_id: int,
        limit: int = 5,
        attempt: int = 1,
    ) -> list[dict]:

        self.require_capability(
            "semantic_memory_search"
        )

        trace = self.start_trace(
            action="semantic_memory_search",
            attempt=attempt,
        metadata={
            "user_id": user_id,
            "limit": limit,
            },
        )

        try:
            retriever = InvestigationRetriever()

            results = retriever.search(
                query=query,
                limit=limit,
                user_id=user_id,
            )

            trace.metadata[
                "result_count"
            ] = len(results)

            trace.complete()

            return results

        except Exception as exc:

            trace.complete(
                status="FAILED",
                error=str(exc),
            )

            raise

    def run(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return the MemoryAgent identity and capabilities.

        Full memory retrieval remains exposed through the
        specialized methods above.
        """

        return {
            "agent": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
        }
