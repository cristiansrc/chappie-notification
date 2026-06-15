"""Unit tests for domain exceptions."""

from chappie_notification.domain.exceptions.domain_exceptions import (
    AgentExecutionError,
    CommandNotAllowedError,
    NotificationError,
    TTSGenerationError,
)


class TestCommandNotAllowedError:
    """Tests for CommandNotAllowedError."""

    def test_is_exception(self) -> None:
        error = CommandNotAllowedError("sudo is not allowed")
        assert isinstance(error, Exception)
        assert str(error) == "sudo is not allowed"


class TestAgentExecutionError:
    """Tests for AgentExecutionError."""

    def test_is_exception(self) -> None:
        error = AgentExecutionError("Agent crashed")
        assert isinstance(error, Exception)
        assert str(error) == "Agent crashed"


class TestTTSGenerationError:
    """Tests for TTSGenerationError."""

    def test_is_exception(self) -> None:
        error = TTSGenerationError("Edge-TTS failed")
        assert isinstance(error, Exception)
        assert str(error) == "Edge-TTS failed"


class TestNotificationError:
    """Tests for NotificationError."""

    def test_is_exception(self) -> None:
        error = NotificationError("notify-send not found")
        assert isinstance(error, Exception)
        assert str(error) == "notify-send not found"
