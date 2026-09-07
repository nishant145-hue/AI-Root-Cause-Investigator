from typing import Any


MAX_INVESTIGATION_ATTEMPTS = 3


def should_continue_investigation(
    state: dict[str, Any],
) -> bool:
    """
    Determine whether the investigation requires
    another investigation cycle.
    """

    status = state.get(
        "investigation_status"
    )

    attempts = state.get(
        "investigation_attempts",
        0,
    )

    if status == "ROOT_CAUSE_VALIDATED":
        return False

    if status == "READY_FOR_VALIDATION":
        return False

    if attempts >= MAX_INVESTIGATION_ATTEMPTS:
        return False

    if status in {
        "MORE_EVIDENCE_REQUIRED",
        "REPLANNING",
    }:
        return True

    return False
