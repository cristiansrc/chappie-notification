"""ExecutionConsumer - consumes chappie.responses queue."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from uuid import UUID

import aio_pika
from aio_pika import Message
from cachetools import TTLCache

from chappie_notification.application.use_cases.process_response import (
    ProcessResponseUseCase,
)
from chappie_notification.domain.models.value_objects import ChappieResponse
from chappie_notification.infrastructure.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class ExecutionConsumer:
    """Consumes messages from chappie.responses and delegates to ProcessResponseUseCase."""

    def __init__(
        self,
        rabbitmq_url: str,
        use_case: ProcessResponseUseCase,
        config: AppConfig,
    ) -> None:
        """Initialize the consumer.

        Args:
            rabbitmq_url: RabbitMQ connection URL.
            use_case: The ProcessResponseUseCase to delegate to.
            config: Application configuration.
        """
        self._rabbitmq_url = rabbitmq_url
        self._use_case = use_case
        self._config = config
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None
        self._consuming_queue: aio_pika.Queue | None = None
        # TTLCache for idempotency: maxsize=10000, ttl=300s (5 minutes)
        self._processed_ids: TTLCache = TTLCache(maxsize=10000, ttl=300)

    async def start(self) -> None:
        """Start consuming messages from chappie.responses."""
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)

        # Declare queue with DLQ configuration
        queue = await self._channel.declare_queue(
            "chappie.responses",
            durable=True,
            arguments={
                "x-message-ttl": 60000,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "chappie.responses.dlq",
            },
        )

        logger.info("ExecutionConsumer started, waiting for messages...")

        await queue.consume(self._on_message)

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        """Process an incoming message.

        Args:
            message: The incoming RabbitMQ message.
        """
        async with message.process(ignore_processed=True):
            try:
                body = message.body
                payload = json.loads(body)

                session_id_str = payload.get("session_id", "")
                timestamp_str = payload.get("timestamp", "")

                # Idempotency check: skip if session_id + timestamp already processed
                idempotency_key = f"{session_id_str}:{timestamp_str}"
                if idempotency_key in self._processed_ids:
                    logger.debug(
                        "Skipping duplicate message",
                        extra={"idempotency_key": idempotency_key},
                    )
                    return

                # Parse into domain model
                response = self._parse_chappie_response(payload)
                if response is None:
                    logger.error("Failed to parse ChappieResponse from message")
                    await message.nack(requeue=False)
                    return

                # Process the response
                result = await self._use_case.execute(response)

                if result.success:
                    # Mark as processed
                    self._processed_ids.add(idempotency_key)
                    logger.info(
                        "Response processed successfully",
                        extra={
                            "session_id": session_id_str,
                            "tts_requested": result.tts_requested,
                            "agent_started": result.agent_started,
                            "command_started": result.command_started,
                        },
                    )
                else:
                    logger.error(
                        "Response processing failed",
                        extra={
                            "session_id": session_id_str,
                            "error": result.error,
                        },
                    )
                    await message.nack(requeue=False)

            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in message", extra={"error": str(e)})
                await message.nack(requeue=False)
            except Exception as e:
                logger.error(
                    "Unhandled error processing message",
                    extra={"error": str(e)},
                )
                await message.nack(requeue=False)

    def _parse_chappie_response(self, payload: dict) -> ChappieResponse | None:
        """Parse a dict payload into a ChappieResponse domain object.

        Args:
            payload: The raw message payload.

        Returns:
            A ChappieResponse or None if parsing fails.
        """
        from chappie_notification.domain.models.enums import NotificationUrgency
        from chappie_notification.domain.models.value_objects import (
            AgentCall,
            MemoryUpdate,
            NotificationRequest,
            TerminalCommand,
        )

        try:
            session_id = UUID(payload["session_id"])
            timestamp = datetime.fromisoformat(payload["timestamp"])

            # Parse agent_call if present
            agent_call = None
            if "agent_call" in payload and payload["agent_call"] is not None:
                ac = payload["agent_call"]
                agent_call = AgentCall(
                    enabled=ac.get("enabled", False),
                    agent=ac.get("agent", ""),
                    prompt=ac.get("prompt", ""),
                    notify_on_complete=ac.get("notify_on_complete", False),
                )

            # Parse terminal_command if present
            terminal_command = None
            if "terminal_command" in payload and payload["terminal_command"] is not None:
                tc = payload["terminal_command"]
                terminal_command = TerminalCommand(
                    enabled=tc.get("enabled", False),
                    command=tc.get("command", ""),
                    requires_confirmation=tc.get("requires_confirmation", False),
                )

            # Parse notification if present
            notification = None
            if "notification" in payload and payload["notification"] is not None:
                n = payload["notification"]
                notification = NotificationRequest(
                    enabled=n.get("enabled", False),
                    title=n.get("title", ""),
                    message=n.get("message", ""),
                    urgency=NotificationUrgency(n.get("urgency", "normal")),
                )

            # Parse memory_update if present
            memory_update = None
            if "memory_update" in payload and payload["memory_update"] is not None:
                mu = payload["memory_update"]
                memory_update = MemoryUpdate(
                    save_to_memory=mu.get("save_to_memory", False),
                    tags=mu.get("tags", []),
                )

            return ChappieResponse(
                session_id=session_id,
                timestamp=timestamp,
                voice_response=payload.get("voice_response", ""),
                agent_call=agent_call,
                terminal_command=terminal_command,
                notification=notification,
                memory_update=memory_update,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to parse ChappieResponse",
                extra={"error": str(e), "payload": payload},
            )
            return None

    async def stop(self) -> None:
        """Stop the consumer and close connections."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("ExecutionConsumer stopped")
