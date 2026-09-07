from typing import Any

from app.agent.agents.base import BaseAgent
from app.agent.reasoning import AgentReasoningService
from app.agent.schemas import HypothesisAnalysisResponse


class ReasonerAgent(BaseAgent):
    """
    Specialized agent responsible for AI-powered
    root-cause hypothesis generation.

    The ReasonerAgent owns hypothesis generation only.

    It receives:
    - incident summary
    - current evidence
    - historical investigation context

    It does not directly retrieve logs or memory.
    """

    name = "reasoner"

    role = (
        "Analyze current evidence and historical context "
        "to generate competing root-cause hypotheses."
    )

    def __init__(self) -> None:
        super().__init__(
            capabilities=[
                "generate_hypotheses",
            ]
        )

    def generate_hypotheses(
        self,
        incident_summary: str,
        evidence: list[dict],
        historical_incidents: list[dict] | None = None,
        attempt: int = 1,
    ) -> HypothesisAnalysisResponse:

        self.require_capability(
            "generate_hypotheses"
        )

        trace = self.start_trace(
            action="generate_hypotheses",
            metadata={
                "evidence_count": len(
                    evidence
                ),
                "historical_count": len(
                    historical_incidents or []
                ),
            },
        )

        try:
            reasoning_service = (
                AgentReasoningService()
            )

            response = (
                reasoning_service.generate_hypotheses(
                    incident_summary=incident_summary,
                    evidence=evidence,
                    historical_incidents=(
                        historical_incidents or []
                    ),
                )
            )

            trace.metadata[
                "hypothesis_count"
            ] = len(response.hypotheses)

            trace.complete()

            return response

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
        Execute reasoning against the current
        investigation state.
        """

        evidence = state.get(
            "evidence",
            [],
        )

        historical_incidents = state.get(
            "historical_incidents",
            [],
        )

        if not evidence:
            return {
                "agent": self.name,
                "status": "NO_EVIDENCE",
                "hypotheses": [],
            }

        response = self.generate_hypotheses(
            incident_summary=(
                state["incident_summary"]
            ),
            evidence=evidence,
            historical_incidents=(
                historical_incidents
            ),
        )

        return {
            "agent": self.name,
            "status": "COMPLETED",
            "hypotheses": response.hypotheses,
        }
