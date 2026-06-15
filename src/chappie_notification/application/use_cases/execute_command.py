"""ExecuteCommandUseCase implementation.

Validates and executes terminal commands, publishing results to RabbitMQ.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from chappie_notification.application.dto.results import ExecuteAgentResult
from chappie_notification.application.ports.command_port import (
    CommandExecutorPort,
    CommandValidatorPort,
)
from chappie_notification.application.ports.messaging_port import RabbitMQPublisherPort
from chappie_notification.domain.exceptions.domain_exceptions import CommandNotAllowedError
from chappie_notification.domain.models.enums import ErrorType, ExecutionStatus
from chappie_notification.domain.models.value_objects import (
    ErrorContext,
    ErrorMessage,
    TerminalCommand,
)
from chappie_notification.infrastructure.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class ExecuteCommandUseCase:
    """Validates and executes a terminal command."""

    def __init__(
        self,
        command_executor: CommandExecutorPort,
        command_validator: CommandValidatorPort,
        rabbitmq_publisher: RabbitMQPublisherPort,
        config: AppConfig,
    ) -> None:
        """Initialize the use case.

        Args:
            command_executor: Port for executing commands.
            command_validator: Port for validating commands against whitelist.
            rabbitmq_publisher: Port for publishing to RabbitMQ.
            config: Application configuration.
        """
        self._command_executor = command_executor
        self._command_validator = command_validator
        self._rabbitmq_publisher = rabbitmq_publisher
        self._config = config

    async def execute(
        self, command: TerminalCommand, session_id: UUID
    ) -> ExecuteAgentResult:
        """Validate and execute a command, then publish the result.

        Args:
            command: The terminal command to execute.
            session_id: The session ID for tracking.

        Returns:
            ExecuteAgentResult with the execution status.

        Raises:
            CommandNotAllowedError: If the command is not in the whitelist.
        """
        logger.info(
            "Executing command",
            extra={
                "session_id": str(session_id),
                "command": command.command,
            },
        )

        # Step 1: Validate command against whitelist
        if not self._command_validator.is_allowed(command.command):
            logger.warning(
                "Command not allowed by whitelist",
                extra={
                    "session_id": str(session_id),
                    "command": command.command,
                },
            )
            # Publish error message
            error_msg = ErrorMessage(
                session_id=session_id,
                timestamp=datetime.now(timezone.utc),
                original_request=command.command,
                error_type=ErrorType.VALIDATION_ERROR,
                error=f"Command not allowed: {command.command}",
                context=ErrorContext(command=command.command),
            )
            await self._rabbitmq_publisher.publish(
                queue="chappie.errors",
                message={
                    "session_id": str(error_msg.session_id),
                    "timestamp": error_msg.timestamp.isoformat(),
                    "original_request": error_msg.original_request,
                    "error_type": error_msg.error_type.value,
                    "error": error_msg.error,
                    "context": {
                        "agent": error_msg.context.agent if error_msg.context else None,
                        "command": error_msg.context.command if error_msg.context else None,
                    },
                },
            )
            raise CommandNotAllowedError(
                f"Command not allowed by whitelist: {command.command}"
            )

        try:
            # Step 2: Execute command
            execution_result = await self._command_executor.execute(
                command=command.command,
                timeout=self._config.command_timeout,
            )

            status = (
                ExecutionStatus.SUCCESS
                if execution_result.exit_code == 0
                else ExecutionStatus.FAILURE
            )
            result_text = execution_result.stdout or execution_result.stderr

            # Publish result to chappie.agent.results
            await self._rabbitmq_publisher.publish(
                queue="chappie.agent.results",
                message={
                    "session_id": str(session_id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": "terminal",
                    "status": status.value,
                    "result": result_text,
                    "notify_user": True,
                },
            )

            # On failure, publish error message
            if status == ExecutionStatus.FAILURE:
                error_msg = ErrorMessage(
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    original_request=command.command,
                    error_type=ErrorType.COMMAND_FAILURE,
                    error=execution_result.stderr or "Command failed",
                    context=ErrorContext(command=command.command),
                )
                await self._rabbitmq_publisher.publish(
                    queue="chappie.errors",
                    message={
                        "session_id": str(error_msg.session_id),
                        "timestamp": error_msg.timestamp.isoformat(),
                        "original_request": error_msg.original_request,
                        "error_type": error_msg.error_type.value,
                        "error": error_msg.error,
                        "context": {
                            "agent": error_msg.context.agent if error_msg.context else None,
                            "command": error_msg.context.command if error_msg.context else None,
                        },
                    },
                )

            return ExecuteAgentResult(
                success=status == ExecutionStatus.SUCCESS,
                status=status,
                result=result_text,
            )

        except CommandNotAllowedError:
            raise
        except Exception as e:
            logger.error(
                "Command execution failed",
                extra={
                    "session_id": str(session_id),
                    "command": command.command,
                    "error": str(e),
                },
            )
            return ExecuteAgentResult(
                success=False,
                status=ExecutionStatus.FAILURE,
                result="",
                error=str(e),
            )
