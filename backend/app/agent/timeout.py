class AgentTimeoutError(TimeoutError):
    """Raised when an agent exceeds its execution timeout."""

    def __init__(
        self,
        agent_name: str,
        timeout_seconds: float,
    ) -> None:
        self.agent_name = agent_name
        self.timeout_seconds = timeout_seconds

        super().__init__(
            f"Agent '{agent_name}' exceeded "
            f"the timeout of {timeout_seconds:.2f} seconds."
        )
