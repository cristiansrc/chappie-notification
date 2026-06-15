"""RabbitMQ publisher adapter using aio-pika."""

from __future__ import annotations

import asyncio
import json
import logging

import aio_pika
from aio_pika import DeliveryMode, Message

logger = logging.getLogger(__name__)


class RabbitMQPublisherAdapter:
    """Publishes messages to RabbitMQ queues using aio-pika."""

    def __init__(self, connection_url: str) -> None:
        """Initialize the publisher.

        Args:
            connection_url: RabbitMQ connection URL.
        """
        self._connection_url = connection_url
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None

    async def _ensure_connection(self) -> aio_pika.Channel:
        """Ensure we have an active connection and channel.

        Returns:
            An active aio-pika channel.
        """
        if self._channel is None or self._channel.is_closed:
            self._connection = await aio_pika.connect_robust(self._connection_url)
            self._channel = await self._connection.channel()
        return self._channel

    async def publish(
        self, queue: str, message: dict, headers: dict | None = None
    ) -> None:
        """Publish a message to a RabbitMQ queue with retry logic.

        Retry: 3 attempts with exponential backoff (1s, 2s, 4s).

        Args:
            queue: Name of the queue to publish to.
            message: JSON-serializable message payload.
            headers: Optional message headers.
        """
        max_retries = 3
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                channel = await self._ensure_connection()

                # Declare queue (durable)
                await channel.declare_queue(queue, durable=True)

                # Serialize message
                body = json.dumps(message, default=str).encode("utf-8")

                # Create message with persistent delivery
                aio_message = Message(
                    body=body,
                    delivery_mode=DeliveryMode.PERSISTENT,
                    headers=headers or {},
                )

                # Publish
                await channel.default_exchange.publish(
                    aio_message,
                    routing_key=queue,
                )
                logger.debug(
                    "Message published to %s",
                    queue,
                    extra={"queue": queue, "message_size": len(body)},
                )
                return

            except Exception as e:
                last_error = e
                logger.warning(
                    "Failed to publish to %s (attempt %d/%d)",
                    queue,
                    attempt + 1,
                    max_retries + 1,
                    extra={"queue": queue, "error": str(e)},
                )
                if attempt < max_retries:
                    backoff = 2 ** attempt  # 1s, 2s, 4s
                    await asyncio.sleep(backoff)

        logger.error(
            "Failed to publish to %s after all retries",
            queue,
            extra={"queue": queue, "error": str(last_error)},
        )

    async def close(self) -> None:
        """Close the connection."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
