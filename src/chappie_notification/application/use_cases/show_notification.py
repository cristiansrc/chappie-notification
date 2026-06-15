"""ShowNotificationUseCase implementation.

Shows interactive notifications using SwayNC and captures user responses.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from chappie_notification.application.dto.results import ShowNotificationResult
from chappie_notification.application.ports.messaging_port import RabbitMQPublisherPort
from chappie_notification.application.ports.notification_port import NotificationSenderPort
from chappie_notification.domain.models.enums import NotificationCategory
from chappie_notification.domain.models.value_objects import (
    AgentAnswer,
    NotificationMessage,
)

logger = logging.getLogger(__name__)


class ShowNotificationUseCase:
    """Shows interactive notifications and captures user responses."""

    def __init__(
        self,
        notification_sender: NotificationSenderPort,
        rabbitmq_publisher: RabbitMQPublisherPort,
    ) -> None:
        """Initialize the use case.

        Args:
            notification_sender: Port for sending notifications.
            rabbitmq_publisher: Port for publishing to RabbitMQ.
        """
        self._notification_sender = notification_sender
        self._rabbitmq_publisher = rabbitmq_publisher

    async def execute(self, notification: NotificationMessage) -> ShowNotificationResult:
        """Show a notification and optionally wait for user response.

        Args:
            notification: The notification message to display.

        Returns:
            ShowNotificationResult with the result of the operation.
        """
        # Build actions as list of dicts for the port
        actions_list = [{"key": a.key, "label": a.label} for a in notification.actions]

        logger.info(
            "Showing notification",
            extra={
                "title": notification.title,
                "category": notification.category.value,
                "actions_count": len(actions_list),
            },
        )

        try:
            # Send notification (returns immediately)
            notification_id = await self._notification_sender.send(
                title=notification.title,
                message=notification.message,
                urgency=notification.urgency.value,
                actions=actions_list,
            )

            # If no actions, fire-and-forget
            if not notification_id or not actions_list:
                return ShowNotificationResult(
                    success=True,
                    notification_id=notification_id,
                )

            # Determine timeout based on category
            if notification.category == NotificationCategory.QUESTION:
                timeout = 600  # 10 minutes for agent questions
            else:
                timeout = 120  # 2 minutes for generic notifications

            # Wait for user action
            user_answer = await self._notification_sender.wait_for_action(
                notification_id=notification_id,
                timeout_seconds=timeout,
            )

            # Default answer on timeout
            if user_answer is None:
                user_answer = "ignore"
                logger.info(
                    "Notification timeout - using default answer",
                    extra={"notification_id": notification_id, "answer": user_answer},
                )

            # If this is an agent question, publish answer to chappie.agent.answers
            if notification.category == NotificationCategory.QUESTION:
                session_id = notification.session_id or uuid4()
                answer = AgentAnswer(
                    notification_id=notification_id,  # type: ignore[arg-type]
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc),
                    answer=user_answer,
                )
                await self._rabbitmq_publisher.publish(
                    queue="chappie.agent.answers",
                    message={
                        "notification_id": str(answer.notification_id),
                        "session_id": str(answer.session_id),
                        "timestamp": answer.timestamp.isoformat(),
                        "answer": answer.answer,
                    },
                )
                logger.info(
                    "Answer published to chappie.agent.answers",
                    extra={"answer": user_answer},
                )

            return ShowNotificationResult(
                success=True,
                notification_id=notification_id,
                user_answer=user_answer,
            )

        except Exception as e:
            logger.error(
                "Failed to show notification",
                extra={"error": str(e)},
            )
            return ShowNotificationResult(
                success=False,
                error=str(e),
            )
