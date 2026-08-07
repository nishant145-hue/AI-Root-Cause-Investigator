from typing import Any
import json


class PromptBuilder:

    @staticmethod
    def build(parsed_logs: Any) -> str:

        logs = json.dumps(parsed_logs, indent=2, ensure_ascii=False)

        prompt = f"""
You are an expert Site Reliability Engineer (SRE),
DevOps Engineer, and Software Architect.

Your task is to investigate the provided application logs.

Return ONLY valid JSON.

Required JSON format:

{{
  "summary": "...",
  "root_cause": "...",
  "failed_component": "...",
  "severity": "...",
  "confidence": 0.95,
  "evidence": [
    {{
      "log_line": "...",
      "reason": "..."
    }}
  ],
  "recommendations": [
    {{
      "title": "...",
      "description": "..."
    }}
  ],
  "additional_notes": "..."
}}

Rules:

1. Never return markdown.
2. Never explain your reasoning.
3. Never wrap JSON in ``` blocks.
4. Use only information from the logs.
5. If uncertain, lower the confidence score.
6. Provide actionable recommendations.

Logs:

{logs}
"""

        return prompt.strip()