from typing import Any

from app.agent.agents.base import BaseAgent


class ValidatorAgent(BaseAgent):
    """
    Specialized agent responsible for validating
    root-cause hypotheses.

    The ValidatorAgent owns only root-cause validation.

    It does not:
    - search logs
    - retrieve historical memory
    - generate hypotheses
    """

    name = "validator"

    role = (
        "Validate the strongest root-cause hypothesis "
        "against the available investigation evidence."
    )

    def __init__(self) -> None:
        super().__init__(
            capabilities=[
                "validate_root_cause",
            ]
        )

    def validate_root_cause(
        self,
        hypotheses: list[dict],
        evidence: list[dict],
        attempt: int = 1,
    ) -> dict:
        """
        Validate the strongest hypothesis against
        the available evidence.
        """

        self.require_capability(
            "validate_root_cause"
        )

        trace = self.start_trace(
            action="validate_root_cause",
            metadata={
                "hypothesis_count": len(
                    hypotheses
                ),
                "evidence_count": len(
                    evidence
                ),
            },
        )

        try:

            if not hypotheses:
                result = {
                    "validated": False,
                    "root_cause": None,
                    "confidence": 0.0,
                    "status": "MORE_EVIDENCE_REQUIRED",
                }

                trace.metadata[
                    "validation_status"
                ] = result["status"]

                trace.complete(
                    status="COMPLETED"
                )

                return result

            strongest = max(
                hypotheses,
                key=lambda item: item.get(
                    "confidence",
                    0.0,
                ),
            )

            supporting = strongest.get(
                "supporting_evidence",
                [],
            )

            contradicting = strongest.get(
                "contradicting_evidence",
                [],
            )

            # A hypothesis without supporting evidence
            #  cannot be validated.
            if not supporting:
                result = {
                    "validated": False,
                    "root_cause": None,
                    "confidence": strongest.get(
                        "confidence",
                        0.0,
                    ),
                    "status": "REJECTED",
                }

                trace.metadata[
                    "validation_status"
                ] = result["status"]

                trace.complete(
                    status="COMPLETED"
                )

                return result

            # Contradicting evidence prevents validation.
            if contradicting:
                result = {
                    "validated": False,
                    "root_cause": None,
                    "confidence": strongest.get(
                        "confidence",
                        0.0,
                    ),
                    "status": "REJECTED",
                }

                trace.metadata[
                    "validation_status"
                ] = result["status"]

                trace.complete(
                    status="COMPLETED"
                )

                return result

            result = {
                "validated": True,
                "root_cause": strongest.get(
                    "cause"
                ),
                "confidence": strongest.get(
                    "confidence",
                    0.0,
                ),
                "status": "ROOT_CAUSE_VALIDATED",
            }

            trace.metadata[
                "validation_status"
            ] = result["status"]

            trace.metadata[
                "confidence"
            ] = result["confidence"]

            trace.complete(
                status="COMPLETED"
            )

            return result

        except Exception as exc:

            trace.complete(
                status="FAILED",
                error=str(exc),
            )

            raise

    def run(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute root-cause validation against the
        current investigation state.
        """

        hypotheses = state.get(
            "hypotheses",
            [],
        )

        evidence = state.get(
            "evidence",
            [],
        )

        result = self.validate_root_cause(
            hypotheses=hypotheses,
            evidence=evidence,
        )

        return {
            "agent": self.name,
            "status": result["status"],
            "validated": result["validated"],
            "root_cause": result["root_cause"],
            "confidence": result["confidence"],
        }
