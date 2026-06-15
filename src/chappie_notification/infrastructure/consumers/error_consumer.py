"""ErrorConsumer - consumes chappie.errors queue."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from uuid import UUID

import aio_pika

from chappie_notification.application.use_cases.handle_error import HandleErrorUseCase
from chappie_notification.domain.models.value_objects import ErrorContext, ErrorMessage
from chappie_notification.infrastructure.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class ErrorConsumer:
    """Consumes messages from chappie.errors and delegates to HandleErrorUseCase."""

    def __init__(
        self,
        rabbitmq_url: str,
        use_case: HandleErrorUseCase,
        config: AppConfig,
    ) -> None:
        """Initialize the consumer.

        Args:
            rabbitmq_url: RabbitMQ connection URL.
            use_case: The HandleErrorUseCase to delegate to.
            config: Application configuration.
        """
        self._rabbitmq_url = rabbitmq_url
        self._use_case = use_case
        self._config = config
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None

    async def start(self) -> None:
        """Start consuming messages from chappie.errors."""
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)

        # Declare queue with DLQ configuration
        queue = await self._channel.declare_queue(
            "chappie.errors",
            durable=True,
            arguments={
                "x-message-ttl": 30000,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "chappie.errors.dlq",
            },
        )

        logger.info("ErrorConsumer started, waiting for messages...")

        await queue.consume(self._on_message)

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        """Process an incoming error message.

        Args:
            message: The incoming RabbitMQ message.
        """
        async with message.process(ignore_processed=True):
            try:
                body = message.body
                payload = json.loads(body)

                # Parse into ErrorMessage domain object
                error = self._parse_error_message(payload)
                if error is None:
                    logger.error("Failed to parse ErrorMessage from payload")
                    await message.nack(requeue=False)
                    return

                # Delegate to HandleErrorUseCase
                result = await self._use_case.execute(error)

                if result.success:
                    logger.info(
                        "Error handled successfully",
                        extra={
                            "session_id": str(error.session_id),
                            "n8n_notified": result.n8n_notified,
                        },
                    )
                else:
                    logger.error(
                        "Error handling failed",
                        extra={
                            "session_id": str(error.session_id),
                            "error": result.error,
                        },
                    )
                    # NACK so message goes to DLQ
                    await message.nack(requeue=False)

            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in error message", extra={"error": str(e)})
                await message.nack(requeue=False)
            except Exception as e:
                logger.error(
                    "Unhandled error in ErrorConsumer",
                    extra={"error": str(e)},
                )
                await message.nack(requeue=False)

    def _parse_error_message(self, payload: dict) -> ErrorMessage | None:
        """Parse a dict payload into an ErrorMessage domain object.

        Args:
            payload: The raw message payload.

        Returns:
            An ErrorMessage or None if parsing fails.
        """
        from chappie_notification.domain.models.enums import ErrorType

        try:
            session_id = UUID(payload["session_id"])
            timestamp = datetime.fromisoformat(payload["timestamp"])

            context = None
            if "context" in payload and payload["context"] is not None:
                ctx = payload["context"]
                context = ErrorContext(
                    agent=ctx.get("agent"),
                    command=ctx.get("command"),
                )

            return ErrorMessage(
                session_id=session_id,
                timestamp=timestamp,
                original_request=payload.get("original_request", ""),
                error_type=ErrorType(payload["error_type"]),
                error=payload.get("error", ""),
                context=context,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to parse ErrorMessage",
                extra={"error": str(e), "payload": payload},
            )
            return None

    async def stop(self) -> None:
        """Stop the consumer and close connections."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("ErrorConsumer stopped")
