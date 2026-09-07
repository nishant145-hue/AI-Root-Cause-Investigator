from dataclasses import dataclass
from enum import Enum

class AgentFailureType(str, Enum):
    TRANSIENT = "TRANSIENT"
    RECOVERABLE = "RECOVERABLE"
    CRITICAL = "CRITICAL"


class RecoveryAction(str, Enum):
    RETRY = "RETRY"
    FALLBACK = "FALLBACK"
    REROUTE = "REROUTE"
    STOP = "STOP"


@dataclass(frozen=True)
class AgentFailure:
    agent: str
    failure_type: AgentFailureType
    message: str
    attempt: int = 1


@dataclass(frozen=True)
class RecoveryDecision:
    action: RecoveryAction
    reason: str
    next_agent: str | None = None

def classify_failure(
    agent: str,
    exc: Exception,
    attempt: int = 1,
) -> AgentFailure:
    """
    Convert an exception into a controlled agent failure.
    """

    message = str(exc)

    transient_errors = (
        TimeoutError,
        ConnectionError,
    )

    if isinstance(exc, transient_errors):
        failure_type = AgentFailureType.TRANSIENT

    elif isinstance(exc, ValueError):
        failure_type = AgentFailureType.RECOVERABLE

    else:
        failure_type = AgentFailureType.CRITICAL

    return AgentFailure(
        agent=agent,
        failure_type=failure_type,
        message=message,
        attempt=attempt,
    )

def determine_recovery(
    failure: AgentFailure,
    max_retries: int = 2,
) -> RecoveryDecision:
    """
    Determine how the investigation should recover
    from an agent failure.
    """

    if failure.failure_type == AgentFailureType.TRANSIENT:

        if failure.attempt <= max_retries:
            return RecoveryDecision(
                action=RecoveryAction.RETRY,
                reason=(
                    f"Transient failure on attempt "
                    f"{failure.attempt}; retry is allowed."
                ),
                next_agent=failure.agent,
            )

        return RecoveryDecision(
            action=RecoveryAction.REROUTE,
            reason=(
                "Transient failure exceeded the "
                "maximum retry limit."
            ),
        )

    if failure.failure_type == AgentFailureType.RECOVERABLE:

        return RecoveryDecision(
            action=RecoveryAction.REROUTE,
            reason=(
                "Recoverable failure; "
                "reroute the investigation."
            ),
        )

    return RecoveryDecision(
        action=RecoveryAction.STOP,
        reason=(
            "Critical failure; "
            "investigation must stop safely."
        ),
    )

@dataclass(frozen=True)
class RetryPolicy:
    """
    Defines retry limits for an agent.
    """

    max_retries: int = 2

    def can_retry(
        self,
        attempt: int,
    ) -> bool:
        """
        Return True when another retry is allowed.
        """

        return attempt <= self.max_retries

class RetryTracker:
    """
    Tracks retry attempts independently for each agent.
    """

    def __init__(
        self,
        policy: RetryPolicy | None = None,
    ) -> None:

        self.policy = (
            policy
            or RetryPolicy()
        )

        self._attempts: dict[str, int] = {}

    def record_failure(
        self,
        agent: str,
    ) -> int:
        """
        Record a failed attempt and return
        the current attempt number.
        """

        attempt = (
            self._attempts.get(agent, 0)
            + 1
        )

        self._attempts[agent] = attempt

        return attempt

    def attempts(
        self,
        agent: str,
    ) -> int:
        """
        Return the current number of failures
        for an agent.
        """

        return self._attempts.get(
            agent,
            0,
        )

    def can_retry(
        self,
        agent: str,
    ) -> bool:
        """
        Determine whether the agent can retry.
        """

        return self.policy.can_retry(
            self.attempts(agent)
        )

    def reset(
        self,
        agent: str,
    ) -> None:
        """
        Reset retry state after successful recovery.
        """

        self._attempts.pop(
            agent,
            None,
        )
