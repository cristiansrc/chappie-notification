"""Command execution and validation port definitions."""

from typing import Protocol, runtime_checkable

from chappie_notification.application.dto.results import CommandExecutionResult


@runtime_checkable
class CommandExecutorPort(Protocol):
    """Port for executing shell commands."""

    async def execute(self, command: str, timeout: int = 30) -> CommandExecutionResult:
        """Execute a shell command.

        Args:
            command: The command to execute.
            timeout: Maximum execution time in seconds.

        Returns:
            Result of the command execution.
        """
        ...


@runtime_checkable
class CommandValidatorPort(Protocol):
    """Port for validating commands against a whitelist."""

    def is_allowed(self, command: str) -> bool:
        """Check if a command is allowed by the whitelist.

        Args:
            command: The command to validate.

        Returns:
            True if the command is allowed, False otherwise.
        """
        ...
