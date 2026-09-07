import json

from app.agent.prompts import build_hypothesis_prompt
from app.agent.schemas import HypothesisAnalysisResponse
from app.exceptions.ai_exceptions import AIValidationError
from app.services.llm.groq_client import GroqClient


class AgentReasoningService:
    """
    Handles LLM-powered hypothesis generation.
    """

    def __init__(self) -> None:
        self.client = GroqClient()

    def generate_hypotheses(
        self,
        incident_summary: str,
        evidence: list[dict],
        historical_incidents: list[dict] | None = None,
    ) -> HypothesisAnalysisResponse:
        """
        Generate hypotheses using current evidence and
        historical investigation context.
        """

        prompt = build_hypothesis_prompt(
            incident_summary=incident_summary,
            evidence=evidence,
            historical_incidents=(
                historical_incidents or []
            ),
        )

        response = self.client.generate(prompt)

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:
            raise AIValidationError(
                "Agent reasoning returned invalid JSON."
            ) from exc

        try:
            return HypothesisAnalysisResponse.model_validate(
                data
            )

        except Exception as exc:
            raise AIValidationError(
                "Agent hypothesis validation failed."
            ) from exc
