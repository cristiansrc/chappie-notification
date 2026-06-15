"""Integration tests for RabbitMQPublisherAdapter.

These tests verify the adapter logic using mocked aio-pika connections.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from chappie_notification.infrastructure.adapters.rabbitmq_publisher_adapter import (
    RabbitMQPublisherAdapter,
)


@pytest.mark.asyncio
class TestRabbitMQPublisherAdapter:
    """Integration tests for RabbitMQPublisherAdapter."""

    async def test_should_publish_message(self) -> None:
        """Test publishing a message to a queue."""
        adapter = RabbitMQPublisherAdapter(
            connection_url="amqp://guest:guest@localhost:5672/"
        )

        with patch.object(adapter, "_ensure_connection") as mock_ensure:
            mock_channel = AsyncMock()
            mock_ensure.return_value = mock_channel

            await adapter.publish(
                queue="chappie.test",
                message={"key": "value"},
            )

            mock_channel.default_exchange.publish.assert_called_once()

    async def test_should_declare_queue(self) -> None:
        """Test that queue is declared before publishing."""
        adapter = RabbitMQPublisherAdapter(
            connection_url="amqp://guest:guest@localhost:5672/"
        )

        with patch.object(adapter, "_ensure_connection") as mock_ensure:
            mock_channel = AsyncMock()
            mock_ensure.return_value = mock_channel

            await adapter.publish(
                queue="chappie.test",
                message={"key": "value"},
            )

            mock_channel.declare_queue.assert_called_once_with(
                "chappie.test", durable=True
            )

    async def test_should_retry_on_connection_failure(self) -> None:
        """Test retry logic when connection fails."""
        adapter = RabbitMQPublisherAdapter(
            connection_url="amqp://guest:guest@localhost:5672/"
        )

        with patch.object(adapter, "_ensure_connection") as mock_ensure:
            mock_ensure.side_effect = [
                ConnectionError("First failure"),
                ConnectionError("Second failure"),
                AsyncMock(),  # Third attempt succeeds
            ]

            await adapter.publish(
                queue="chappie.test",
                message={"key": "value"},
            )

            assert mock_ensure.call_count == 3
