"""ProcessResponseUseCase implementation.

Orchestrates the processing of a ChappieResponse by delegating to
specialized use cases for agent execution, command execution, and TTS.
"""

from __future__ import annotations

import logging
from uuid import UUID

from chappie_notification.application.dto.results import ProcessResponseResult
from chappie_notification.application.ports.messaging_port import RabbitMQPublisherPort
from chappie_notification.application.use_cases.execute_agent import ExecuteAgentUseCase
from chappie_notification.application.use_cases.execute_command import ExecuteCommandUseCase
from chappie_notification.domain.models.value_objects import ChappieResponse

logger = logging.getLogger(__name__)


class ProcessResponseUseCase:
    """Processes a ChappieResponse and delegates actions to appropriate use cases."""

    def __init__(
        self,
        rabbitmq_publisher: RabbitMQPublisherPort,
        execute_agent_uc: ExecuteAgentUseCase,
        execute_command_uc: ExecuteCommandUseCase,
    ) -> None:
        """Initialize the use case.

        Args:
            rabbitmq_publisher: Port for publishing to RabbitMQ.
            execute_agent_uc: Use case for executing agents.
            execute_command_uc: Use case for executing commands.
        """
        self._rabbitmq_publisher = rabbitmq_publisher
        self._execute_agent_uc = execute_agent_uc
        self._execute_command_uc = execute_command_uc

    async def execute(self, response: ChappieResponse) -> ProcessResponseResult:
        """Process a ChappieResponse and delegate actions.

        Args:
            response: The ChappieResponse to process.

        Returns:
            ProcessResponseResult with flags indicating what actions were taken.
        """
        session_id: UUID = response.session_id
        tts_requested = False
        agent_started = False
        command_started = False

        try:
            # Handle agent call
            if response.agent_call and response.agent_call.enabled:
                logger.info(
                    "Starting agent execution",
                    extra={"session_id": str(session_id), "agent": response.agent_call.agent},
                )
                await self._execute_agent_uc.execute(response.agent_call, session_id)
                agent_started = True

            # Handle terminal command
            if response.terminal_command and response.terminal_command.enabled:
                logger.info(
                    "Starting command execution",
                    extra={
                        "session_id": str(session_id),
                        "command": response.terminal_command.command,
                    },
                )
                await self._execute_command_uc.execute(response.terminal_command, session_id)
                command_started = True

            # Handle notification request (not directly processed here)
            if response.notification and response.notification.enabled:
                logger.warning(
                    "Notification action received but not directly processed; "
                    "use notification consumer for interactive notifications",
                    extra={
                        "session_id": str(session_id),
                        "title": response.notification.title,
                    },
                )

            # Handle memory update (not directly processed here)
            if response.memory_update and response.memory_update.save_to_memory:
                logger.warning(
                    "Memory update action received but not directly processed; "
                    "future: delegate to memory service",
                    extra={
                        "session_id": str(session_id),
                        "tags": response.memory_update.tags,
                    },
                )

            # Handle voice response - publish TTS request to RabbitMQ
            if response.voice_response:
                tts_message = {
                    "session_id": str(session_id),
                    "timestamp": response.timestamp.isoformat(),
                    "text": response.voice_response,
                    "priority": "normal",
                    "ducking": True,
                    "show_text": True,
                }
                await self._rabbitmq_publisher.publish(
                    queue="chappie.tts.requests",
                    message=tts_message,
                )
                tts_requested = True
                logger.info(
                    "TTS request published",
                    extra={"session_id": str(session_id)},
                )

            return ProcessResponseResult(
                success=True,
                tts_requested=tts_requested,
                agent_started=agent_started,
                command_started=command_started,
            )

        except Exception as e:
            logger.error(
                "Error processing response",
                extra={"session_id": str(session_id), "error": str(e)},
            )
            return ProcessResponseResult(
                success=False,
                tts_requested=tts_requested,
                agent_started=agent_started,
                command_started=command_started,
                error=str(e),
            )
