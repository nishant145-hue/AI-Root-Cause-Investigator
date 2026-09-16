from app.agent.state import InvestigationState
from app.agent.state_timeline import (
    execute_timeline_operation,
    propagate_timeline,
)


def validator_node(
    state: InvestigationState,
) -> dict:
    """
    Validate the strongest hypothesis.

    This first version performs deterministic validation.
    LLM-based validation will be added later.
    """

    hypotheses = state.get("hypotheses", [])

    if not hypotheses:
        _, trace_entry = execute_timeline_operation(
            state,
            agent="validator",
            action="validate_root_cause",
            metadata={
                "business_status": "REJECTED",
                "reason": "No hypothesis available",
            },
            operation=lambda: None,
        )

        timeline_entry = {
            **trace_entry,
            "status": "REJECTED",
            "reason": "No hypothesis available",
        }

        updated_timeline = propagate_timeline(
            state,
            [timeline_entry],
        )["execution_timeline"]

        return {
            "current_step": "Validation failed",
            "investigation_status": "VALIDATION_FAILED",
            "remaining_questions": [
                "No hypothesis available for validation."
            ],
            "execution_timeline": updated_timeline,
        }

    def validate_hypothesis():
        strongest = max(
            hypotheses,
            key=lambda hypothesis: hypothesis["confidence"],
        )

        confidence = strongest["confidence"]

        return strongest, confidence

    (strongest, confidence), trace_entry = (
        execute_timeline_operation(
            state,
            agent="validator",
            action="validate_root_cause",
            metadata={
                "hypothesis_count": len(hypotheses),
                "validation_threshold": 0.70,
            },
            operation=validate_hypothesis,
        )
    )

    if confidence >= 0.70:
        validated_hypotheses = [
            {
                **hypothesis,
                "status": (
                    "VALIDATED"
                    if hypothesis is strongest
                    else hypothesis["status"]
                ),
            }
            for hypothesis in hypotheses
        ]
        timeline_entry = {
            **trace_entry,
            "status": "COMPLETED",
            "confidence": confidence,
            "root_cause": strongest["cause"],
        }
        updated_timeline = propagate_timeline(
            state,
            [timeline_entry],
        )["execution_timeline"]

        return {
                "hypotheses": validated_hypotheses,
                "root_cause": strongest["cause"],
                "confidence": confidence,
                "failed_component": state.get(
                    "failed_component"
                ),
                "severity": state.get(
                    "severity"
                ),
                "current_step": "Root cause validated",
                "investigation_status": "ROOT_CAUSE_VALIDATED",
                "remaining_questions": [],
                "execution_timeline": updated_timeline,
            }

    timeline_entry = {
        **trace_entry,
        "status": "REJECTED",
        "confidence": confidence,
    }
    updated_timeline = propagate_timeline(
    state,
    [timeline_entry],
)["execution_timeline"]

    return {
    "current_step": "Validation failed",
    "investigation_status": "VALIDATION_FAILED",
    "remaining_questions": [
        "The strongest hypothesis does not have "
        "enough confidence for validation."
    ],
    "execution_timeline": updated_timeline,
}
