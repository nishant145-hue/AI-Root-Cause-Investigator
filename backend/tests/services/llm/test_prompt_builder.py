import pytest
from app.services.llm.prompt_builder import PromptBuilder


def test_build_prompt_success():
    parsed_logs = [
        {
            "timestamp": "2026-08-06T10:00:00",
            "level": "ERROR",
            "component": "Database",
            "message": "Connection pool exhausted.",
        },
        {
            "timestamp": "2026-08-06T10:01:00",
            "level": "ERROR",
            "component": "Replication",
            "message": "Replication lag detected.",
        },
    ]

    prompt = PromptBuilder.build(parsed_logs)

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    
def test_prompt_contains_log_messages():
    parsed_logs = [
        {
            "timestamp": "2026-08-06T10:00:00",
            "level": "ERROR",
            "component": "Database",
            "message": "Connection pool exhausted.",
        }
    ]

    prompt = PromptBuilder.build(parsed_logs)

    assert "Connection pool exhausted." in prompt
    
def test_prompt_contains_required_instructions():
    prompt = PromptBuilder.build([])

    assert "Return ONLY valid JSON" in prompt
    assert "summary" in prompt
    assert "root_cause" in prompt
    assert "Site Reliability Engineer" in prompt
    
def test_empty_logs():
    prompt = PromptBuilder.build([])

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    

        
def test_prompt_is_deterministic():
    parsed_logs = [
        {
            "timestamp": "2026-08-06T10:00:00",
            "level": "ERROR",
            "component": "Database",
            "message": "Connection pool exhausted.",
        }
    ]

    prompt1 = PromptBuilder.build(parsed_logs)
    prompt2 = PromptBuilder.build(parsed_logs)

    assert prompt1 == prompt2