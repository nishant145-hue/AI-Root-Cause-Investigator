import logging
from typing import Any

from app.exceptions.ai_exceptions import AIError
from app.services.llm.groq_client import GroqClient
from app.services.llm.prompt_builder import PromptBuilder
from app.services.llm.response_parser import ResponseParser
from app.services.llm.schemas import AIInvestigationResponse
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class AIService:
    """Coordinates the AI investigation workflow."""

    def __init__(self) -> None:
        self.client = GroqClient()

    def investigate(
        self,
        parsed_logs: Any,
    ) -> AIInvestigationResponse:

        logger.info("AI investigation started.")

        self._validate_logs(parsed_logs)

        prompt = PromptBuilder.build(parsed_logs)

        response = self.client.generate(prompt)

        result = ResponseParser.parse(response)

        logger.info("AI investigation completed successfully.")

        return result
    
    def _validate_logs(
    self,
    parsed_logs: list[dict],
) -> None:

        if not parsed_logs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No parsed logs available for AI investigation.",
            )

        if len(parsed_logs) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many log entries for a single AI investigation.",
            )