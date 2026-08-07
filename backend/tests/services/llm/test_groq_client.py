from unittest.mock import MagicMock, patch

import pytest

from app.exceptions.ai_exceptions import AIConnectionError
from app.services.llm.groq_client import GroqClient
from groq import APIConnectionError, APIStatusError, RateLimitError


def mock_success_response():
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"summary":"success"}'
            )
        )
    ]
    return response


@patch("app.services.llm.groq_client.time.sleep")
def test_generate_success(mock_sleep):
    client = GroqClient()

    client.client.chat.completions.create = MagicMock(
        return_value=mock_success_response()
    )

    result = client.generate("Test prompt")

    assert result == '{"summary":"success"}'

    client.client.chat.completions.create.assert_called_once()

    mock_sleep.assert_not_called()


@patch("app.services.llm.groq_client.time.sleep")
def test_retry_then_success(mock_sleep):
    client = GroqClient()

    client.client.chat.completions.create = MagicMock(
        side_effect=[
            APIConnectionError(
                message="Connection failed",
                request=MagicMock(),
            ),
            mock_success_response(),
        ]
    )

    result = client.generate("Test prompt")

    assert result == '{"summary":"success"}'

    assert client.client.chat.completions.create.call_count == 2

    mock_sleep.assert_called_once()


@patch("app.services.llm.groq_client.time.sleep")
def test_retry_exhausted_connection_error(mock_sleep):
    client = GroqClient()

    client.client.chat.completions.create = MagicMock(
        side_effect=APIConnectionError(
            message="Connection failed",
            request=MagicMock(),
        )
    )

    with pytest.raises(AIConnectionError):
        client.generate("Prompt")


@patch("app.services.llm.groq_client.time.sleep")
def test_retry_exhausted_rate_limit(mock_sleep):
    client = GroqClient()

    response = MagicMock()
    body = {}

    client.client.chat.completions.create = MagicMock(
        side_effect=RateLimitError(
            message="Rate limited",
            response=response,
            body=body,
        )
    )

    with pytest.raises(AIConnectionError):
        client.generate("Prompt")


@patch("app.services.llm.groq_client.time.sleep")
def test_retry_exhausted_status_error(mock_sleep):
    client = GroqClient()

    response = MagicMock()

    client.client.chat.completions.create = MagicMock(
        side_effect=APIStatusError(
            message="Internal error",
            response=response,
            body={},
        )
    )

    with pytest.raises(AIConnectionError):
        client.generate("Prompt")


@patch("app.services.llm.groq_client.time.sleep")
def test_exponential_backoff(mock_sleep):
    client = GroqClient()

    client.client.chat.completions.create = MagicMock(
        side_effect=APIConnectionError(
            message="Connection failed",
            request=MagicMock(),
        )
    )

    with pytest.raises(AIConnectionError):
        client.generate("Prompt")

    assert mock_sleep.call_count >= 1