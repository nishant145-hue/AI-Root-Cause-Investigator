import json


def build_hypothesis_prompt(
    incident_summary: str,
    evidence: list[dict],
    historical_incidents: list[dict] | None = None,
) -> str:
    """
    Build the prompt used by the agent's LLM reasoner.

    Historical incidents are confidence-aware supporting context.
    They must never automatically determine the current root cause.
    """

    evidence_json = json.dumps(
        evidence,
        indent=2,
        ensure_ascii=False,
    )

    historical_incidents = (
        historical_incidents or []
    )

    historical_json = json.dumps(
        historical_incidents,
        indent=2,
        ensure_ascii=False,
    )

    return f"""
You are an expert Site Reliability Engineer.

Analyze the current incident using:

1. Current incident information
2. Current evidence
3. Similar historical investigations

Your task is to generate possible root-cause hypotheses.

Historical investigations are ONLY supporting context.

A historical incident must NOT be treated as proof
that the current incident has the same root cause.

========================================================
HISTORICAL MEMORY RELIABILITY
========================================================

Historical memories contain confidence and quality metadata.

Memory status meanings:

RELIABLE:
- Memory quality is 0.80 or higher.
- Strong historical context.
- May provide meaningful supporting evidence.
- Still must be verified against current evidence.

USEFUL:
- Memory quality is between 0.60 and 0.79.
- Potentially useful supporting context.
- Must NOT be treated as proof.
- Current evidence has higher priority.

WEAK:
- Memory quality is below 0.60.
- Do not use as meaningful evidence.
- Do not increase hypothesis confidence because of it.

STALE:
- Historical information is old or unreliable.
- Do not use it to support a hypothesis.

Only historical incidents explicitly supplied in the
SIMILAR HISTORICAL INVESTIGATIONS section may be considered.

========================================================
CONFIDENCE RULES
========================================================

When evaluating a hypothesis:

1. Current evidence has the highest priority.
2. Strong current evidence can increase confidence.
3. Contradicting current evidence must reduce confidence.
4. RELIABLE historical memory may provide supporting context.
5. USEFUL historical memory may provide weak supporting context.
6. WEAK or STALE memory must not increase confidence.
7. Historical similarity alone must never validate a hypothesis.
8. Do not copy the confidence of a historical investigation
   into the current hypothesis.
9. Confidence must reflect the current incident.
10. If current evidence is insufficient, lower confidence.

========================================================
GENERAL INVESTIGATION RULES
========================================================

1. Use only the supplied information.
2. Do not invent evidence.
3. Consider multiple hypotheses when reasonable.
4. Confidence must be between 0 and 1.
5. Strong current evidence should receive more weight
   than historical similarity.
6. Historical incidents may support a hypothesis but
   cannot independently validate it.
7. Consider alternative explanations.
8. Explicitly consider contradicting evidence.
9. Do not treat historical root causes as confirmed
   causes of the current incident.
10. Return ONLY valid JSON.
11. Do not use markdown.

========================================================
HYPOTHESIS OUTPUT
========================================================

For each hypothesis provide:

- cause
- confidence between 0 and 1
- supporting evidence
- contradicting evidence

Required format:

{{
    "hypotheses": [
        {{
            "cause": "...",
            "confidence": 0.75,
            "supporting_evidence": [
                "..."
            ],
            "contradicting_evidence": [
                "..."
            ]
        }}
    ]
}}

========================================================
CURRENT INCIDENT
========================================================

{incident_summary}

========================================================
CURRENT EVIDENCE
========================================================

{evidence_json}

========================================================
SIMILAR HISTORICAL INVESTIGATIONS
========================================================

{historical_json}

========================================================
FINAL REMINDER
========================================================

Current evidence is more important than historical memory.

Historical memory is context, not proof.

Do not increase confidence solely because a historical
incident looks similar.

Return ONLY valid JSON.
""".strip()
