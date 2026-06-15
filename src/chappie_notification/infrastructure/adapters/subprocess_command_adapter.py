"""Subprocess command executor adapter."""

from __future__ import annotations

import asyncio
import logging

from chappie_notification.application.dto.results import CommandExecutionResult

logger = logging.getLogger(__name__)


class SubprocessCommandExecutorAdapter:
    """Executes shell commands using asyncio.subprocess."""

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the adapter.

        Args:
            timeout: Default timeout for command execution.
        """
        self._default_timeout = timeout

    async def execute(
        self, command: str, timeout: int = 30
    ) -> CommandExecutionResult:
        """Execute a shell command.

        Args:
            command: The command to execute.
            timeout: Maximum execution time in seconds.

        Returns:
            CommandExecutionResult with stdout, stderr, and exit code.
        """
        effective_timeout = timeout or self._default_timeout

        logger.info(
            "Executing command",
            extra={"command": command, "timeout": effective_timeout},
        )

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                logger.warning("Command timed out", extra={"command": command})
                return CommandExecutionResult(
                    success=False,
                    stdout="",
                    stderr="timeout",
                    exit_code=-1,
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

            return CommandExecutionResult(
                success=process.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode or 0,
            )

        except Exception as e:
            logger.error(
                "Command execution failed",
                extra={"command": command, "error": str(e)},
            )
            return CommandExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
            )
