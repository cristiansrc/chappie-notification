"""TTSConsumer - consumes chappie.tts.requests queue."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import aio_pika

from chappie_notification.application.use_cases.generate_tts import GenerateTTSUseCase
from chappie_notification.domain.models.enums import ErrorType, TTSPriority
from chappie_notification.domain.models.value_objects import (
    ErrorContext,
    ErrorMessage,
    TTSRequest,
)
from chappie_notification.infrastructure.config.app_config import AppConfig
from chappie_notification.infrastructure.adapters.rabbitmq_publisher_adapter import (
    RabbitMQPublisherAdapter,
)

logger = logging.getLogger(__name__)


class TTSConsumer:
    """Consumes messages from chappie.tts.requests and delegates to GenerateTTSUseCase."""

    def __init__(
        self,
        rabbitmq_url: str,
        use_case: GenerateTTSUseCase,
        publisher: RabbitMQPublisherAdapter,
        config: AppConfig,
    ) -> None:
        """Initialize the consumer.

        Args:
            rabbitmq_url: RabbitMQ connection URL.
            use_case: The GenerateTTSUseCase to delegate to.
            publisher: Publisher for sending error messages.
            config: Application configuration.
        """
        self._rabbitmq_url = rabbitmq_url
        self._use_case = use_case
        self._publisher = publisher
        self._config = config
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None

    async def start(self) -> None:
        """Start consuming messages from chappie.tts.requests."""
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)

        # Declare queue with DLQ configuration
        queue = await self._channel.declare_queue(
            "chappie.tts.requests",
            durable=True,
            arguments={
                "x-message-ttl": 30000,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "chappie.tts.requests.dlq",
            },
        )

        logger.info("TTSConsumer started, waiting for messages...")

        await queue.consume(self._on_message)

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        """Process an incoming TTS request message.

        Args:
            message: The incoming RabbitMQ message.
        """
        async with message.process(ignore_processed=True):
            try:
                body = message.body
                payload = json.loads(body)

                # Parse into TTSRequest domain object
                tts_request = self._parse_tts_request(payload)
                if tts_request is None:
                    logger.error("Failed to parse TTSRequest from payload")
                    await message.nack(requeue=False)
                    return

                # Generate TTS
                result = await self._use_case.execute(tts_request)

                if result.success:
                    logger.info(
                        "TTS generation successful",
                        extra={
                            "session_id": str(tts_request.session_id),
                            "audio_path": result.audio_path,
                        },
                    )
                else:
                    logger.error(
                        "TTS generation failed",
                        extra={
                            "session_id": str(tts_request.session_id),
                            "error": result.error,
                        },
                    )
                    # Publish error to chappie.errors
                    error_msg = ErrorMessage(
                        session_id=tts_request.session_id,
                        timestamp=datetime.now(timezone.utc),
                        original_request=tts_request.text,
                        error_type=ErrorType.AGENT_FAILURE,
                        error=result.error or "TTS generation failed",
                        context=ErrorContext(command=None),
                    )
                    await self._publisher.publish(
                        queue="chappie.errors",
                        message={
                            "session_id": str(error_msg.session_id),
                            "timestamp": error_msg.timestamp.isoformat(),
                            "original_request": error_msg.original_request,
                            "error_type": error_msg.error_type.value,
                            "error": error_msg.error,
                            "context": {
                                "agent": error_msg.context.agent if error_msg.context else None,
                                "command": error_msg.context.command
                                if error_msg.context
                                else None,
                            },
                        },
                    )

            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in TTS request", extra={"error": str(e)})
                await message.nack(requeue=False)
            except Exception as e:
                logger.error(
                    "Unhandled error in TTSConsumer",
                    extra={"error": str(e)},
                )
                await message.nack(requeue=False)

    def _parse_tts_request(self, payload: dict) -> TTSRequest | None:
        """Parse a dict payload into a TTSRequest domain object.

        Args:
            payload: The raw message payload.

        Returns:
            A TTSRequest or None if parsing fails.
        """
        try:
            return TTSRequest(
                session_id=UUID(payload["session_id"]),
                timestamp=datetime.fromisoformat(payload["timestamp"]),
                text=payload.get("text", ""),
                priority=TTSPriority(payload.get("priority", "normal")),
                ducking=payload.get("ducking", False),
                show_text=payload.get("show_text", False),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to parse TTSRequest",
                extra={"error": str(e), "payload": payload},
            )
            return None

    async def stop(self) -> None:
        """Stop the consumer and close connections."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("TTSConsumer stopped")
