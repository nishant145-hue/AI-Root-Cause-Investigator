import json

from app.exceptions.ai_exceptions import AIValidationError
from app.services.llm.schemas import AIInvestigationResponse
from pydantic import ValidationError


class ResponseParser:
    """Parse and validate LLM responses."""

    @staticmethod
    def parse(response: str) -> AIInvestigationResponse:

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:
            raise AIValidationError(
                "LLM returned invalid JSON."
        ) from exc

        try:
            return AIInvestigationResponse.model_validate(data)

        except ValidationError as exc:
            raise AIValidationError(
                "LLM response validation failed."
            ) from exc