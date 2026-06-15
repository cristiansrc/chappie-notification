"""Unit tests for domain value objects."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from chappie_notification.domain.models.enums import (
    ErrorType,
    ExecutionStatus,
    NotificationCategory,
    NotificationUrgency,
    TTSPriority,
)
from chappie_notification.domain.models.value_objects import (
    AgentAnswer,
    AgentCall,
    AgentQuestion,
    AgentResult,
    ChappieResponse,
    ErrorContext,
    ErrorMessage,
    MemoryUpdate,
    NotificationAction,
    NotificationMessage,
    NotificationRequest,
    QuestionOption,
    TerminalCommand,
    TTSRequest,
)


class TestChappieResponse:
    """Tests for ChappieResponse."""

    def test_create_with_all_fields(self) -> None:
        session_id = uuid4()
        now = datetime.now()
        response = ChappieResponse(
            session_id=session_id,
            timestamp=now,
            voice_response="Hello",
            agent_call=AgentCall(
                enabled=True, agent="dev", prompt="test", notify_on_complete=False
            ),
            terminal_command=TerminalCommand(
                enabled=False, command="ls", requires_confirmation=False
            ),
            notification=NotificationRequest(
                enabled=True, title="Test", message="Test msg", urgency=NotificationUrgency.NORMAL
            ),
            memory_update=MemoryUpdate(save_to_memory=True, tags=["test"]),
        )
        assert response.session_id == session_id
        assert response.timestamp == now
        assert response.voice_response == "Hello"
        assert response.agent_call is not None
        assert response.agent_call.enabled is True

    def test_create_with_minimal_fields(self) -> None:
        session_id = uuid4()
        now = datetime.now()
        response = ChappieResponse(
            session_id=session_id,
            timestamp=now,
            voice_response="",
        )
        assert response.agent_call is None
        assert response.terminal_command is None
        assert response.notification is None
        assert response.memory_update is None

    def test_frozen(self) -> None:
        session_id = uuid4()
        response = ChappieResponse(
            session_id=session_id,
            timestamp=datetime.now(),
            voice_response="test",
        )
        with pytest.raises(AttributeError):
            response.voice_response = "modified"  # type: ignore[misc]


class TestAgentCall:
    """Tests for AgentCall."""

    def test_create(self) -> None:
        ac = AgentCall(
            enabled=True,
            agent="code-reviewer",
            prompt="Review this code",
            notify_on_complete=True,
        )
        assert ac.enabled is True
        assert ac.agent == "code-reviewer"
        assert ac.prompt == "Review this code"
        assert ac.notify_on_complete is True


class TestTerminalCommand:
    """Tests for TerminalCommand."""

    def test_create(self) -> None:
        tc = TerminalCommand(
            enabled=True,
            command="ls -la",
            requires_confirmation=False,
        )
        assert tc.enabled is True
        assert tc.command == "ls -la"


class TestTTSRequest:
    """Tests for TTSRequest."""

    def test_create(self) -> None:
        req = TTSRequest(
            session_id=uuid4(),
            timestamp=datetime.now(),
            text="Hello world",
            priority=TTSPriority.NORMAL,
            ducking=True,
            show_text=True,
        )
        assert req.text == "Hello world"
        assert req.priority == TTSPriority.NORMAL
        assert req.ducking is True


class TestErrorMessage:
    """Tests for ErrorMessage."""

    def test_create_with_context(self) -> None:
        err = ErrorMessage(
            session_id=uuid4(),
            timestamp=datetime.now(),
            original_request="run agent",
            error_type=ErrorType.AGENT_FAILURE,
            error="Agent crashed",
            context=ErrorContext(agent="dev"),
        )
        assert err.error_type == ErrorType.AGENT_FAILURE
        assert err.context is not None
        assert err.context.agent == "dev"

    def test_create_without_context(self) -> None:
        err = ErrorMessage(
            session_id=uuid4(),
            timestamp=datetime.now(),
            original_request="run agent",
            error_type=ErrorType.COMMAND_FAILURE,
            error="Command failed",
        )
        assert err.context is None


class TestNotificationMessage:
    """Tests for NotificationMessage."""

    def test_create_with_actions(self) -> None:
        notification = NotificationMessage(
            timestamp=datetime.now(),
            title="Test",
            message="Message",
            urgency=NotificationUrgency.CRITICAL,
            actions=[
                NotificationAction(key="yes", label="Yes"),
                NotificationAction(key="no", label="No"),
            ],
            category=NotificationCategory.QUESTION,
        )
        assert len(notification.actions) == 2
        assert notification.actions[0].key == "yes"


class TestAgentQuestion:
    """Tests for AgentQuestion."""

    def test_create(self) -> None:
        q = AgentQuestion(
            session_id=uuid4(),
            timestamp=datetime.now(),
            agent="helper",
            question="Continue?",
            options=[QuestionOption(key="y", label="Yes")],
            notification_id=uuid4(),
        )
        assert q.agent == "helper"
        assert q.options[0].key == "y"


class TestAgentAnswer:
    """Tests for AgentAnswer."""

    def test_create(self) -> None:
        answer = AgentAnswer(
            notification_id=uuid4(),
            session_id=uuid4(),
            timestamp=datetime.now(),
            answer="apply",
        )
        assert answer.answer == "apply"


class TestAgentResult:
    """Tests for AgentResult."""

    def test_create(self) -> None:
        result = AgentResult(
            session_id=uuid4(),
            timestamp=datetime.now(),
            agent="dev",
            status=ExecutionStatus.SUCCESS,
            result="Done",
            notify_user=True,
        )
        assert result.status == ExecutionStatus.SUCCESS
        assert result.notify_user is True
