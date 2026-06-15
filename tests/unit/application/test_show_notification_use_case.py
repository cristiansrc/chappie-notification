"""Unit tests for ShowNotificationUseCase."""

from datetime import datetime
from unittest.mock import ANY, AsyncMock
from uuid import uuid4

import pytest

from chappie_notification.application.use_cases.show_notification import (
    ShowNotificationUseCase,
)
from chappie_notification.domain.models.enums import NotificationCategory, NotificationUrgency
from chappie_notification.domain.models.value_objects import (
    NotificationAction,
    NotificationMessage,
)


@pytest.fixture
def use_case(
    mock_notification_sender: AsyncMock,
    mock_rabbitmq_publisher: AsyncMock,
) -> ShowNotificationUseCase:
    return ShowNotificationUseCase(
        notification_sender=mock_notification_sender,
        rabbitmq_publisher=mock_rabbitmq_publisher,
    )


_SESSION_ID = uuid4()


class TestShowNotificationUseCase:
    """Tests for ShowNotificationUseCase."""

    @pytest.mark.asyncio
    async def test_should_show_fire_and_forget_notification(
        self,
        use_case: ShowNotificationUseCase,
        mock_notification_sender: AsyncMock,
        mock_rabbitmq_publisher: AsyncMock,
    ) -> None:
        notification = NotificationMessage(
            timestamp=datetime.now(),
            title="Test",
            message="Test message",
            urgency=NotificationUrgency.NORMAL,
            actions=[],
            category=NotificationCategory.INFO,
            session_id=_SESSION_ID,
        )
        mock_notification_sender.send.return_value = None
        result = await use_case.execute(notification)
        assert result.success is True
        mock_notification_sender.send.assert_called_once()
        mock_rabbitmq_publisher.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_wait_for_action_on_question(
        self,
        use_case: ShowNotificationUseCase,
        mock_notification_sender: AsyncMock,
        mock_rabbitmq_publisher: AsyncMock,
    ) -> None:
        notification = NotificationMessage(
            timestamp=datetime.now(),
            title="Question",
            message="Continue?",
            urgency=NotificationUrgency.CRITICAL,
            actions=[
                NotificationAction(key="yes", label="Yes"),
                NotificationAction(key="no", label="No"),
            ],
            category=NotificationCategory.QUESTION,
            session_id=_SESSION_ID,
        )
        mock_notification_sender.send.return_value = "notification-123"
        mock_notification_sender.wait_for_action.return_value = "yes"

        result = await use_case.execute(notification)
        assert result.success is True
        assert result.user_answer == "yes"
        mock_notification_sender.wait_for_action.assert_called_once()
        mock_rabbitmq_publisher.publish.assert_called_once_with(
            queue="chappie.agent.answers",
            message={
                "notification_id": "notification-123",
                "session_id": str(_SESSION_ID),
                "timestamp": ANY,
                "answer": "yes",
            },
        )

    @pytest.mark.asyncio
    async def test_should_generate_uuid_when_no_session_id(
        self,
        use_case: ShowNotificationUseCase,
        mock_notification_sender: AsyncMock,
        mock_rabbitmq_publisher: AsyncMock,
    ) -> None:
        """Test that a UUID is generated when notification has no session_id."""
        notification = NotificationMessage(
            timestamp=datetime.now(),
            title="Question",
            message="Continue?",
            urgency=NotificationUrgency.CRITICAL,
            actions=[NotificationAction(key="yes", label="Yes")],
            category=NotificationCategory.QUESTION,
            session_id=None,
        )
        mock_notification_sender.send.return_value = "notification-456"
        mock_notification_sender.wait_for_action.return_value = "yes"

        result = await use_case.execute(notification)
        assert result.success is True
        assert result.user_answer == "yes"
        # Should have been called with a generated UUID
        publish_call = mock_rabbitmq_publisher.publish.call_args
        assert publish_call is not None
        session_id_in_msg = publish_call.kwargs["message"]["session_id"]
        # Should be a valid UUID string, not empty
        assert session_id_in_msg != ""
        # Verify it parses as UUID
        from uuid import UUID
        assert UUID(session_id_in_msg)

    @pytest.mark.asyncio
    async def test_should_use_ignore_on_timeout(
        self,
        use_case: ShowNotificationUseCase,
        mock_notification_sender: AsyncMock,
    ) -> None:
        notification = NotificationMessage(
            timestamp=datetime.now(),
            title="Question",
            message="Continue?",
            urgency=NotificationUrgency.CRITICAL,
            actions=[NotificationAction(key="y", label="Yes")],
            category=NotificationCategory.QUESTION,
            session_id=_SESSION_ID,
        )
        mock_notification_sender.send.return_value = "notification-123"
        mock_notification_sender.wait_for_action.return_value = None

        result = await use_case.execute(notification)
        assert result.success is True
        assert result.user_answer == "ignore"
