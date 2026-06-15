"""Integration tests for RabbitMQ consumers.

These tests verify consumer logic using mocked dependencies.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chappie_notification.application.use_cases.generate_tts import GenerateTTSUseCase
from chappie_notification.application.use_cases.handle_error import HandleErrorUseCase
from chappie_notification.application.use_cases.process_response import ProcessResponseUseCase
from chappie_notification.application.use_cases.show_notification import ShowNotificationUseCase
from chappie_notification.domain.models.value_objects import (
    ChappieResponse,
    ErrorMessage,
    TTSRequest,
)
from chappie_notification.infrastructure.consumers.error_consumer import ErrorConsumer
from chappie_notification.infrastructure.consumers.execution_consumer import ExecutionConsumer
from chappie_notification.infrastructure.consumers.notification_consumer import (
    NotificationConsumer,
)
from chappie_notification.infrastructure.consumers.tts_consumer import TTSConsumer
from chappie_notification.infrastructure.adapters.rabbitmq_publisher_adapter import (
    RabbitMQPublisherAdapter,
)


@pytest.fixture
def mock_publisher() -> AsyncMock:
    return AsyncMock(spec=RabbitMQPublisherAdapter)


@pytest.mark.asyncio
class TestConsumers:
    """Integration tests for message consumers using mocked dependencies."""

    async def test_execution_consumer_parses_valid_message(self, test_config) -> None:
        """Test ExecutionConsumer can parse a valid ChappieResponse from a payload."""
        mock_use_case = AsyncMock(spec=ProcessResponseUseCase)
        consumer = ExecutionConsumer(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            use_case=mock_use_case,
            config=test_config,
        )

        session_id = uuid4()
        payload = {
            "session_id": str(session_id),
            "timestamp": datetime.now().isoformat(),
            "voice_response": "Hello world",
        }
        response = consumer._parse_chappie_response(payload)
        assert response is not None
        assert isinstance(response, ChappieResponse)
        assert response.session_id == session_id
        assert response.voice_response == "Hello world"

    async def test_execution_consumer_returns_none_on_invalid_payload(
        self, test_config
    ) -> None:
        """Test ExecutionConsumer returns None for an invalid payload."""
        mock_use_case = AsyncMock(spec=ProcessResponseUseCase)
        consumer = ExecutionConsumer(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            use_case=mock_use_case,
            config=test_config,
        )

        payload = {"invalid": "data"}
        response = consumer._parse_chappie_response(payload)
        assert response is None

    async def test_error_consumer_parses_error_message(self, test_config) -> None:
        """Test ErrorConsumer can parse a valid ErrorMessage from a payload."""
        mock_use_case = AsyncMock(spec=HandleErrorUseCase)
        consumer = ErrorConsumer(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            use_case=mock_use_case,
            config=test_config,
        )

        session_id = uuid4()
        payload = {
            "session_id": str(session_id),
            "timestamp": datetime.now().isoformat(),
            "original_request": "test request",
            "error_type": "agent_failure",
            "error": "Agent failed",
        }
        error = consumer._parse_error_message(payload)
        assert error is not None
        assert isinstance(error, ErrorMessage)
        assert error.session_id == session_id
        assert error.error_type.value == "agent_failure"

    async def test_error_consumer_returns_none_on_invalid_payload(
        self, test_config
    ) -> None:
        """Test ErrorConsumer returns None for an invalid payload."""
        mock_use_case = AsyncMock(spec=HandleErrorUseCase)
        consumer = ErrorConsumer(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            use_case=mock_use_case,
            config=test_config,
        )

        payload = {"invalid": "data"}
        error = consumer._parse_error_message(payload)
        assert error is None

    async def test_tts_consumer_parses_tts_request(self, test_config) -> None:
        """Test TTSConsumer can parse a valid TTSRequest from a payload."""
        mock_use_case = AsyncMock(spec=GenerateTTSUseCase)
        consumer = TTSConsumer(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            use_case=mock_use_case,
            publisher=AsyncMock(),
            config=test_config,
        )

        session_id = uuid4()
        payload = {
            "session_id": str(session_id),
            "timestamp": datetime.now().isoformat(),
            "text": "Hello world",
            "priority": "normal",
            "ducking": True,
            "show_text": True,
        }
        tts_request = consumer._parse_tts_request(payload)
        assert tts_request is not None
        assert isinstance(tts_request, TTSRequest)
        assert tts_request.session_id == session_id
        assert tts_request.text == "Hello world"

    async def test_tts_consumer_returns_none_on_invalid_payload(
        self, test_config
    ) -> None:
        """Test TTSConsumer returns None for an invalid payload."""
        mock_use_case = AsyncMock(spec=GenerateTTSUseCase)
        consumer = TTSConsumer(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            use_case=mock_use_case,
            publisher=AsyncMock(),
            config=test_config,
        )

        payload = {"invalid": "data"}
        tts_request = consumer._parse_tts_request(payload)
        assert tts_request is None

    async def test_notification_consumer_delegates_to_use_case(
        self, test_config, mock_publisher: AsyncMock
    ) -> None:
        """Test NotificationConsumer delegates to ShowNotificationUseCase."""
        mock_use_case = AsyncMock(spec=ShowNotificationUseCase)
        consumer = NotificationConsumer(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            use_case=mock_use_case,
            publisher=mock_publisher,
            config=test_config,
        )

        payload = {
            "agent": "dev",
            "status": "success",
            "result": "All tests passed",
            "session_id": str(uuid4()),
        }
        await consumer._on_agent_result(payload)
        assert mock_use_case.execute.called
