from typing import Any

from app.agent.agents.base import BaseAgent
from app.agent.nodes.investigator import search_logs
from app.agent.state_timeline import (
    propagate_timeline,
)


class InvestigatorAgent(BaseAgent):
    """
    Specialized agent responsible for log investigation.

    The InvestigatorAgent owns only log-search capabilities.
    """

    name = "investigator"

    role = (
        "Investigate application logs and collect "
        "observations and evidence."
    )

    def __init__(self) -> None:
        super().__init__(
            capabilities=[
                "search_logs",
            ]
        )

    def search_logs(
        self,
        session: Any,
        log_file_id: int,
        query: str | None = None,
        severity: str | None = None,
        component: str | None = None,
        limit: int = 50,
        attempt: int = 1,
    ) -> list[dict]:

        self.require_capability(
            "search_logs"
        )

        trace = self.start_trace(
            action="search_logs",
            attempt=attempt,
        metadata={
            "log_file_id": log_file_id,
            "query": query,
            "severity": severity,
            "component": component,
            "limit": limit,
        },
    )

        try:
            results = search_logs(
                session=session,
                log_file_id=log_file_id,
                query=query,
                severity=severity,
                component=component,
                limit=limit,
            )

            trace.metadata[
                "result_count"
            ] = len(results)

            trace.complete(
                status="COMPLETED"
            )

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
        Execute the specialized investigator interface.

        The existing investigator node remains responsible
        for the complete investigation workflow.
        """

        return {
            "agent": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
        }
