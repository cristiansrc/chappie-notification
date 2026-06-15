"""Agent executor port definition."""

from typing import Protocol, runtime_checkable

from chappie_notification.application.dto.results import AgentExecutionResult


@runtime_checkable
class AgentExecutorPort(Protocol):
    """Port for executing OpenCode agents."""

    async def execute(self, agent: str, prompt: str, timeout: int = 120) -> AgentExecutionResult:
        """Execute an OpenCode agent.

        Args:
            agent: The agent name to execute.
            prompt: The prompt to send to the agent.
            timeout: Maximum execution time in seconds.

        Returns:
            Result of the agent execution.
        """
        ...
