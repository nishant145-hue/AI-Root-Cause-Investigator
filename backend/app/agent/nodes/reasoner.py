from app.agent.reasoning import AgentReasoningService
from app.agent.state import InvestigationState
from app.agent.state_timeline import (
    propagate_timeline,
)


def reasoner_node(
    state: InvestigationState,
) -> dict:
    """
    Generate root-cause hypotheses using the LLM.

    The LLM receives:
    - current incident
    - current evidence
    - historical similar incidents
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
        timeline_entry = {
            "agent": "reasoner",
            "action": "generate_hypotheses",
            "status": "NO_EVIDENCE",
            "hypothesis_count": 0,
        }

        updated_timeline = propagate_timeline(
            state,
            [timeline_entry],
        )["execution_timeline"]

        return {
            "hypotheses": [],
            "current_step": "No evidence available",
            "investigation_status": (
                "MORE_EVIDENCE_REQUIRED"
            ),
            "execution_timeline": updated_timeline,
        }

    reasoning_service = AgentReasoningService()

    response = reasoning_service.generate_hypotheses(
        incident_summary=(
            state["incident_summary"]
        ),
        evidence=evidence,
        historical_incidents=(
            historical_incidents
        ),
    )

    hypotheses = []

    for item in response.hypotheses:

        hypotheses.append(
            {
                "cause": item.cause,
                "confidence": item.confidence,
                "supporting_evidence": (
                    item.supporting_evidence
                ),
                "contradicting_evidence": (
                    item.contradicting_evidence
                ),
                "status": "CANDIDATE",
            }
        )

    hypotheses.sort(
        key=lambda hypothesis: hypothesis[
            "confidence"
        ],
        reverse=True,
    )

    timeline_entry = {
        "agent": "reasoner",
        "action": "generate_hypotheses",
        "status": "COMPLETED",
        "hypothesis_count": len(hypotheses),
    }

    updated_timeline = propagate_timeline(
        state,
        [timeline_entry],
    )["execution_timeline"]

    return {
        "hypotheses": hypotheses,
        "current_step": (
            "Reflect on competing hypotheses"
        ),
        "investigation_status": "REASONING",
        "execution_timeline": updated_timeline,
    }
