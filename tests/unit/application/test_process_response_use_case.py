"""Unit tests for ProcessResponseUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chappie_notification.application.use_cases.process_response import (
    ProcessResponseUseCase,
)
from chappie_notification.domain.models.enums import NotificationUrgency, TTSPriority
from chappie_notification.domain.models.value_objects import (
    AgentCall,
    ChappieResponse,
    MemoryUpdate,
    NotificationRequest,
    TerminalCommand,
)


@pytest.fixture
def use_case(mock_rabbitmq_publisher: AsyncMock) -> ProcessResponseUseCase:
    mock_agent_uc = AsyncMock()
    mock_command_uc = AsyncMock()
    return ProcessResponseUseCase(
        rabbitmq_publisher=mock_rabbitmq_publisher,
        execute_agent_uc=mock_agent_uc,
        execute_command_uc=mock_command_uc,
    )


class TestProcessResponseUseCase:
    """Tests for ProcessResponseUseCase."""

    @pytest.mark.asyncio
    async def test_should_return_success_when_all_actions_disabled(
        self, use_case: ProcessResponseUseCase, mock_rabbitmq_publisher: AsyncMock
    ) -> None:
        response = ChappieResponse(
            session_id=uuid4(),
            timestamp=datetime.now(),
            voice_response="",
        )
        result = await use_case.execute(response)
        assert result.success is True
        assert result.tts_requested is False
        assert result.agent_started is False
        assert result.command_started is False
        mock_rabbitmq_publisher.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_publish_tts_when_voice_response(
        self, use_case: ProcessResponseUseCase, mock_rabbitmq_publisher: AsyncMock
    ) -> None:
        response = ChappieResponse(
            session_id=uuid4(),
            timestamp=datetime.now(),
            voice_response="Hello world",
        )
        result = await use_case.execute(response)
        assert result.success is True
        assert result.tts_requested is True
        mock_rabbitmq_publisher.publish.assert_called_once_with(
            queue="chappie.tts.requests",
            message={
                "session_id": str(response.session_id),
                "timestamp": response.timestamp.isoformat(),
                "text": "Hello world",
                "priority": "normal",
                "ducking": True,
                "show_text": True,
            },
        )

    @pytest.mark.asyncio
    async def test_should_delegate_to_agent_use_case(
        self, use_case: ProcessResponseUseCase, mock_rabbitmq_publisher: AsyncMock
    ) -> None:
        session_id = uuid4()
        now = datetime.now()
        response = ChappieResponse(
            session_id=session_id,
            timestamp=now,
            voice_response="",
            agent_call=AgentCall(
                enabled=True,
                agent="dev",
                prompt="run tests",
                notify_on_complete=True,
            ),
        )
        result = await use_case.execute(response)
        assert result.agent_started is True
        # Should have called execute_agent_uc.execute
        use_case._execute_agent_uc.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_delegate_to_command_use_case(
        self, use_case: ProcessResponseUseCase, mock_rabbitmq_publisher: AsyncMock
    ) -> None:
        session_id = uuid4()
        response = ChappieResponse(
            session_id=session_id,
            timestamp=datetime.now(),
            voice_response="",
            terminal_command=TerminalCommand(
                enabled=True,
                command="ls -la",
                requires_confirmation=False,
            ),
        )
        result = await use_case.execute(response)
        assert result.command_started is True
        use_case._execute_command_uc.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_log_warning_on_notification(
        self, use_case: ProcessResponseUseCase, mock_rabbitmq_publisher: AsyncMock, caplog
    ) -> None:
        """Test that a warning is logged when notification is present."""
        import logging
        caplog.set_level(logging.WARNING)

        response = ChappieResponse(
            session_id=uuid4(),
            timestamp=datetime.now(),
            voice_response="",
            notification=NotificationRequest(
                enabled=True,
                title="Test notification",
                message="Hello",
                urgency=NotificationUrgency.NORMAL,
            ),
        )
        result = await use_case.execute(response)
        assert result.success is True
        # Check that a warning was logged about notification
        assert any(
            "Notification action received" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_should_log_warning_on_memory_update(
        self, use_case: ProcessResponseUseCase, mock_rabbitmq_publisher: AsyncMock, caplog
    ) -> None:
        """Test that a warning is logged when memory_update is present."""
        import logging
        caplog.set_level(logging.WARNING)

        response = ChappieResponse(
            session_id=uuid4(),
            timestamp=datetime.now(),
            voice_response="",
            memory_update=MemoryUpdate(
                save_to_memory=True,
                tags=["test", "example"],
            ),
        )
        result = await use_case.execute(response)
        assert result.success is True
        # Check that a warning was logged about memory update
        assert any(
            "Memory update action received" in record.message
            for record in caplog.records
        )
