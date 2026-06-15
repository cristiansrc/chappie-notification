"""OpenCode agent executor adapter using subprocess."""

from __future__ import annotations

import asyncio
import logging
import shlex

from chappie_notification.application.dto.results import AgentExecutionResult

logger = logging.getLogger(__name__)


class OpenCodeAgentExecutorAdapter:
    """Executes OpenCode agents using subprocess."""

    def __init__(self, timeout: int = 120) -> None:
        """Initialize the adapter.

        Args:
            timeout: Default timeout for agent execution.
        """
        self._default_timeout = timeout

    async def execute(
        self, agent: str, prompt: str, timeout: int = 120
    ) -> AgentExecutionResult:
        """Execute an OpenCode agent.

        Runs: opencode run --agent <agent> "<prompt>"

        Args:
            agent: The agent name to execute.
            prompt: The prompt to send to the agent.
            timeout: Maximum execution time in seconds.

        Returns:
            AgentExecutionResult with stdout, stderr, and exit code.
        """
        effective_timeout = timeout or self._default_timeout

        # Build command - subprocess handles argument escaping automatically
        cmd = ["opencode", "run", "--agent", agent, prompt]

        logger.info(
            "Executing OpenCode agent",
            extra={"agent": agent, "prompt_length": len(prompt), "timeout": effective_timeout},
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
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
                logger.warning("Agent execution timed out", extra={"agent": agent})
                return AgentExecutionResult(
                    success=False,
                    stdout="",
                    stderr="timeout",
                    exit_code=-1,
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

            exit_code = process.returncode if process.returncode is not None else -1
            return AgentExecutionResult(
                success=process.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
            )

        except FileNotFoundError:
            logger.error("opencode binary not found", extra={"agent": agent})
            return AgentExecutionResult(
                success=False,
                stdout="",
                stderr="opencode: command not found",
                exit_code=-1,
            )
        except Exception as e:
            logger.error(
                "Agent execution failed",
                extra={"agent": agent, "error": str(e)},
            )
            return AgentExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
            )
