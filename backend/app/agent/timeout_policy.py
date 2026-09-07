from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class AgentTimeoutPolicy:
    """Central timeout configuration for agent execution."""

    agent_timeout_seconds: float
    investigation_timeout_seconds: float
    recovery_timeout_seconds: float

    @classmethod
    def from_settings(cls) -> "AgentTimeoutPolicy":
        return cls(
            agent_timeout_seconds=(
                settings.AGENT_TIMEOUT_SECONDS
            ),
            investigation_timeout_seconds=(
                settings.INVESTIGATION_TIMEOUT_SECONDS
            ),
            recovery_timeout_seconds=(
                settings.RECOVERY_TIMEOUT_SECONDS
            ),
        )

    def timeout_for(self, operation: str) -> float:
        """Return the configured timeout for an operation."""

        if operation == "agent":
            return self.agent_timeout_seconds

        if operation == "investigation":
            return self.investigation_timeout_seconds

        if operation == "recovery":
            return self.recovery_timeout_seconds

        raise ValueError(
            f"Unknown timeout operation: {operation}"
        )
