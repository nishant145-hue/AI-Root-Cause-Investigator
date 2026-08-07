import json

import pytest

from app.exceptions.ai_exceptions import AIValidationError
from app.services.llm.response_parser import ResponseParser
from app.services.llm.schemas import AIInvestigationResponse


def valid_response():
    return {
        "summary": "Database connection pool exhaustion caused failures.",
        "root_cause": "Blocked schema migration exhausted the pool.",
        "failed_component": "Database",
        "severity": "Critical",
        "confidence": 0.95,
        "additional_notes": "Increase pool size."
    }


def test_parse_valid_response():
    response = json.dumps(valid_response())

    result = ResponseParser.parse(response)

    assert isinstance(result, AIInvestigationResponse)
    assert result.summary == valid_response()["summary"]
    assert result.root_cause == valid_response()["root_cause"]


def test_invalid_json():
    with pytest.raises(AIValidationError):
        ResponseParser.parse("This is not JSON")


def test_missing_required_fields():
    response = json.dumps(
        {
            "summary": "Only summary present."
        }
    )

    with pytest.raises(AIValidationError):
        ResponseParser.parse(response)


def test_invalid_confidence_type():
    response = valid_response()
    response["confidence"] = "high"

    with pytest.raises(AIValidationError):
        ResponseParser.parse(json.dumps(response))


def test_parser_is_deterministic():
    response = json.dumps(valid_response())

    result1 = ResponseParser.parse(response)
    result2 = ResponseParser.parse(response)

    assert result1 == result2