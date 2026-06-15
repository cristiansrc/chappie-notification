"""RabbitMQ publisher port definition."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class RabbitMQPublisherPort(Protocol):
    """Port for publishing messages to RabbitMQ queues."""

    async def publish(self, queue: str, message: dict, headers: dict | None = None) -> None:
        """Publish a message to a RabbitMQ queue.

        Args:
            queue: Name of the queue to publish to.
            message: JSON-serializable message payload.
            headers: Optional message headers.
        """
        ...
