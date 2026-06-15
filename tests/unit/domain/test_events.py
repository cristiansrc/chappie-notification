"""Unit tests for domain events."""

from datetime import datetime
from uuid import uuid4

from chappie_notification.domain.events.domain_events import (
    AgentExecutionCompleted,
    AgentExecutionStarted,
    TTSGenerationRequested,
)
from chappie_notification.domain.models.enums import ExecutionStatus, TTSPriority


class TestAgentExecutionStarted:
    """Tests for AgentExecutionStarted event."""

    def test_create(self) -> None:
        session_id = uuid4()
        now = datetime.now()
        event = AgentExecutionStarted(
            session_id=session_id,
            agent="dev",
            timestamp=now,
        )
        assert event.session_id == session_id
        assert event.agent == "dev"
        assert event.timestamp == now


class TestAgentExecutionCompleted:
    """Tests for AgentExecutionCompleted event."""

    def test_create(self) -> None:
        session_id = uuid4()
        now = datetime.now()
        event = AgentExecutionCompleted(
            session_id=session_id,
            agent="dev",
            status=ExecutionStatus.SUCCESS,
            result="Completed",
            timestamp=now,
        )
        assert event.status == ExecutionStatus.SUCCESS
        assert event.result == "Completed"


class TestTTSGenerationRequested:
    """Tests for TTSGenerationRequested event."""

    def test_create(self) -> None:
        session_id = uuid4()
        now = datetime.now()
        event = TTSGenerationRequested(
            session_id=session_id,
            text="Hello",
            priority=TTSPriority.NORMAL,
            timestamp=now,
        )
        assert event.text == "Hello"
        assert event.priority == TTSPriority.NORMAL
