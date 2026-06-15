"""ExecuteAgentUseCase implementation.

Executes an OpenCode agent and publishes results to RabbitMQ.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from chappie_notification.application.dto.results import ExecuteAgentResult
from chappie_notification.application.ports.agent_port import AgentExecutorPort
from chappie_notification.application.ports.messaging_port import RabbitMQPublisherPort
from chappie_notification.domain.models.enums import ErrorType, ExecutionStatus
from chappie_notification.domain.models.value_objects import (
    AgentCall,
    ErrorContext,
    ErrorMessage,
)
from chappie_notification.infrastructure.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class ExecuteAgentUseCase:
    """Executes an OpenCode agent and publishes results."""

    def __init__(
        self,
        agent_executor: AgentExecutorPort,
        rabbitmq_publisher: RabbitMQPublisherPort,
        config: AppConfig,
    ) -> None:
        """Initialize the use case.

        Args:
            agent_executor: Port for executing agents.
            rabbitmq_publisher: Port for publishing to RabbitMQ.
            config: Application configuration.
        """
        self._agent_executor = agent_executor
        self._rabbitmq_publisher = rabbitmq_publisher
        self._config = config

    async def execute(self, agent_call: AgentCall, session_id: UUID) -> ExecuteAgentResult:
        """Execute an agent and publish the result.

        Args:
            agent_call: The agent call configuration.
            session_id: The session ID for tracking.

        Returns:
            ExecuteAgentResult with the execution status.
        """
        logger.info(
            "Executing agent",
            extra={
                "session_id": str(session_id),
                "agent": agent_call.agent,
            },
        )

        try:
            # Execute agent via port
            execution_result = await self._agent_executor.execute(
                agent=agent_call.agent,
                prompt=agent_call.prompt,
                timeout=self._config.agent_timeout,
            )

            if execution_result.success:
                status = ExecutionStatus.SUCCESS
                result_text = execution_result.stdout
                logger.info(
                    "Agent execution succeeded",
                    extra={"session_id": str(session_id), "agent": agent_call.agent},
                )
            else:
                status = ExecutionStatus.FAILURE
                result_text = execution_result.stderr or "Unknown error"
                logger.warning(
                    "Agent execution failed",
                    extra={
                        "session_id": str(session_id),
                        "agent": agent_call.agent,
                        "error": result_text,
                    },
                )

            # Publish result to chappie.agent.results
            await self._rabbitmq_publisher.publish(
                queue="chappie.agent.results",
                message={
                    "session_id": str(session_id),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": agent_call.agent,
                    "status": status.value,
                    "result": result_text,
                    "notify_user": agent_call.notify_on_complete,
                },
            )

            # On failure, publish error message
            if status == ExecutionStatus.FAILURE:
                error_msg = ErrorMessage(
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    original_request=agent_call.prompt,
                    error_type=ErrorType.AGENT_FAILURE,
                    error=result_text,
                    context=ErrorContext(agent=agent_call.agent),
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

        except Exception as e:
            logger.error(
                "Agent execution raised exception",
                extra={
                    "session_id": str(session_id),
                    "agent": agent_call.agent,
                    "error": str(e),
                },
            )
            return ExecuteAgentResult(
                success=False,
                status=ExecutionStatus.FAILURE,
                result="",
                error=str(e),
            )
