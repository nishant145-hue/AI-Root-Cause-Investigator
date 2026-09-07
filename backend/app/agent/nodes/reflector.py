from app.agent.state import InvestigationState


MIN_EVIDENCE = 2
MIN_CONFIDENCE = 0.70


def reflector_node(
    state: InvestigationState,
) -> dict:
    """
    Evaluate whether the current investigation has
    sufficient evidence to move toward validation.
    """

    evidence = state.get("evidence", [])
    hypotheses = state.get("hypotheses", [])

    if not hypotheses:
        return {
            "remaining_questions": [
                "No root-cause hypotheses have been generated."
            ],
            "investigation_status": "MORE_EVIDENCE_REQUIRED",
        }

    strongest = max(
        hypotheses,
        key=lambda hypothesis: hypothesis["confidence"],
    )

    strongest_confidence = strongest["confidence"]

    remaining_questions: list[str] = []

    if len(evidence) < MIN_EVIDENCE:
        remaining_questions.append(
            "Collect additional supporting evidence."
        )

    if strongest_confidence < MIN_CONFIDENCE:
        remaining_questions.append(
            "Increase confidence in the strongest hypothesis."
        )

    if len(hypotheses) == 1:
        remaining_questions.append(
            "Check for alternative root-cause explanations."
        )

    if remaining_questions:
        return {
            "remaining_questions": remaining_questions,
            "investigation_status": "MORE_EVIDENCE_REQUIRED",
        }

    return {
        "remaining_questions": [],
        "confidence": strongest_confidence,
        "investigation_status": "READY_FOR_VALIDATION",
    }
