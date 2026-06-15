"""Shared test fixtures for chappie-notification tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from chappie_notification.infrastructure.config.app_config import AppConfig


@pytest.fixture
def test_config() -> AppConfig:
    """Return an AppConfig instance with test-appropriate defaults."""
    return AppConfig(
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        daemon_base_url="http://localhost:8765",
        n8n_base_url="http://localhost:5678",
        n8n_webhook_secret="test_secret",
        tts_voice="es-AR-ElenaNeural",
        tts_output_path="/tmp/test_chappie_tts.mp3",
        tts_text_path="/tmp/test_chappie_tts_text.txt",
        whitelist_path="./config/commands-whitelist.yaml",
        agent_timeout=120,
        command_timeout=30,
        http_timeout=10,
    )


@pytest.fixture
def mock_rabbitmq_publisher() -> AsyncMock:
    """Return a mock RabbitMQPublisherPort."""
    return AsyncMock()


@pytest.fixture
def mock_tts_synthesizer() -> AsyncMock:
    """Return a mock TTSSynthesizerPort."""
    mock = AsyncMock()
    mock.synthesize.return_value = "/tmp/test_chappie_tts.mp3"
    return mock


@pytest.fixture
def mock_agent_executor() -> AsyncMock:
    """Return a mock AgentExecutorPort."""
    from chappie_notification.application.dto.results import AgentExecutionResult

    mock = AsyncMock()
    mock.execute.return_value = AgentExecutionResult(
        success=True,
        stdout="Agent completed successfully",
        stderr="",
        exit_code=0,
    )
    return mock


@pytest.fixture
def mock_command_executor() -> AsyncMock:
    """Return a mock CommandExecutorPort."""
    from chappie_notification.application.dto.results import CommandExecutionResult

    mock = AsyncMock()
    mock.execute.return_value = CommandExecutionResult(
        success=True,
        stdout="Command completed",
        stderr="",
        exit_code=0,
    )
    return mock


@pytest.fixture
def mock_command_validator() -> MagicMock:
    """Return a mock CommandValidatorPort."""
    mock = MagicMock()
    mock.is_allowed.return_value = True
    return mock


@pytest.fixture
def mock_notification_sender() -> AsyncMock:
    """Return a mock NotificationSenderPort."""
    mock = AsyncMock()
    mock.send.return_value = "test-notification-id"
    mock.wait_for_action.return_value = "apply"
    return mock


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Return a mock HTTPClientPort."""
    mock = AsyncMock()
    mock.post.return_value = {"status": "ok"}
    return mock


@pytest.fixture
def mock_file_writer() -> AsyncMock:
    """Return a mock FileWriterPort."""
    return AsyncMock()
