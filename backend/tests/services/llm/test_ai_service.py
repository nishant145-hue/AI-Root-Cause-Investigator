from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.llm.ai_service import AIService
from app.services.llm.schemas import AIInvestigationResponse


def parsed_logs():
    return [
        {
            "timestamp": "2026-08-06T10:00:00",
            "severity": "ERROR",
            "source": "Database",
            "component": "ConnectionPool",
            "message": "Connection pool exhausted.",
        }
    ]


def ai_result():
    return AIInvestigationResponse(
        summary="Database issue",
        root_cause="Connection pool exhausted",
        failed_component="Database",
        severity="Critical",
        confidence=0.95,
        additional_notes="Increase pool size.",
    )


@patch("app.services.llm.ai_service.ResponseParser.parse")
@patch("app.services.llm.ai_service.GroqClient.generate")
@patch("app.services.llm.ai_service.PromptBuilder.build")
def test_investigate_success(
    mock_build,
    mock_generate,
    mock_parse,
):
    mock_build.return_value = "PROMPT"

    mock_generate.return_value = '{"summary":"ok"}'

    mock_parse.return_value = ai_result()

    service = AIService()

    result = service.investigate(parsed_logs())

    assert result.summary == "Database issue"

    mock_build.assert_called_once()

    mock_generate.assert_called_once_with("PROMPT")

    mock_parse.assert_called_once()


def test_validate_empty_logs():

    service = AIService()

    with pytest.raises(HTTPException):

        service.investigate([])


def test_validate_too_many_logs():

    service = AIService()

    logs = [{}] * 501

    with pytest.raises(HTTPException):

        service.investigate(logs)


@patch("app.services.llm.ai_service.ResponseParser.parse")
@patch("app.services.llm.ai_service.GroqClient.generate")
@patch("app.services.llm.ai_service.PromptBuilder.build")
def test_prompt_builder_called(
    mock_build,
    mock_generate,
    mock_parse,
):

    mock_build.return_value = "PROMPT"

    mock_generate.return_value = '{"summary":"ok"}'

    mock_parse.return_value = ai_result()

    AIService().investigate(parsed_logs())

    mock_build.assert_called_once()


@patch("app.services.llm.ai_service.ResponseParser.parse")
@patch("app.services.llm.ai_service.GroqClient.generate")
@patch("app.services.llm.ai_service.PromptBuilder.build")
def test_groq_client_called(
    mock_build,
    mock_generate,
    mock_parse,
):

    mock_build.return_value = "PROMPT"

    mock_generate.return_value = '{"summary":"ok"}'

    mock_parse.return_value = ai_result()

    AIService().investigate(parsed_logs())

    mock_generate.assert_called_once_with("PROMPT")


@patch("app.services.llm.ai_service.ResponseParser.parse")
@patch("app.services.llm.ai_service.GroqClient.generate")
@patch("app.services.llm.ai_service.PromptBuilder.build")
def test_response_parser_called(
    mock_build,
    mock_generate,
    mock_parse,
):

    mock_build.return_value = "PROMPT"

    mock_generate.return_value = '{"summary":"ok"}'

    mock_parse.return_value = ai_result()

    AIService().investigate(parsed_logs())

    mock_parse.assert_called_once()