"""Unit tests for domain enums."""

from chappie_notification.domain.models.enums import (
    ErrorType,
    ExecutionStatus,
    NotificationCategory,
    NotificationUrgency,
    TTSPriority,
)


class TestTTSPriority:
    """Tests for TTSPriority enum."""

    def test_values(self) -> None:
        assert TTSPriority.NORMAL.value == "normal"
        assert TTSPriority.HIGH.value == "high"

    def test_str_inheritance(self) -> None:
        assert TTSPriority.NORMAL.value == "normal"
        assert TTSPriority.HIGH.value == "high"
        assert str(TTSPriority.NORMAL) == "TTSPriority.NORMAL"


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_values(self) -> None:
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILURE.value == "failure"

    def test_str_inheritance(self) -> None:
        assert ExecutionStatus.SUCCESS.value == "success"
        assert str(ExecutionStatus.SUCCESS) == "ExecutionStatus.SUCCESS"


class TestErrorType:
    """Tests for ErrorType enum."""

    def test_values(self) -> None:
        assert ErrorType.AGENT_FAILURE.value == "agent_failure"
        assert ErrorType.COMMAND_FAILURE.value == "command_failure"
        assert ErrorType.VALIDATION_ERROR.value == "validation_error"


class TestNotificationUrgency:
    """Tests for NotificationUrgency enum."""

    def test_values(self) -> None:
        assert NotificationUrgency.LOW.value == "low"
        assert NotificationUrgency.NORMAL.value == "normal"
        assert NotificationUrgency.CRITICAL.value == "critical"


class TestNotificationCategory:
    """Tests for NotificationCategory enum."""

    def test_values(self) -> None:
        assert NotificationCategory.AGENT_COMPLETE.value == "agent_complete"
        assert NotificationCategory.ERROR.value == "error"
        assert NotificationCategory.INFO.value == "info"
        assert NotificationCategory.QUESTION.value == "question"
