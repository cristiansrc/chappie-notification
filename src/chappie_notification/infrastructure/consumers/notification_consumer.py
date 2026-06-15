"""NotificationConsumer - consumes chappie.agent.results, chappie.agent.questions, chappie.notifications."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID

import aio_pika

from chappie_notification.application.use_cases.show_notification import (
    ShowNotificationUseCase,
)
from chappie_notification.domain.models.enums import NotificationCategory, NotificationUrgency
from chappie_notification.domain.models.value_objects import (
    NotificationAction,
    NotificationMessage,
)
from chappie_notification.infrastructure.config.app_config import AppConfig
from chappie_notification.infrastructure.adapters.rabbitmq_publisher_adapter import (
    RabbitMQPublisherAdapter,
)

logger = logging.getLogger(__name__)


def _parse_uuid(value: str | None) -> UUID | None:
    """Parse a string value into a UUID, returning None on failure.

    Args:
        value: The string value to parse.

    Returns:
        A UUID instance or None if the value is invalid or missing.
    """
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, TypeError):
        logger.warning("Invalid UUID value", extra={"value": value})
        return None


class NotificationConsumer:
    """Consumes messages from three queues and shows notifications."""

    def __init__(
        self,
        rabbitmq_url: str,
        use_case: ShowNotificationUseCase,
        publisher: RabbitMQPublisherAdapter,
        config: AppConfig,
    ) -> None:
        """Initialize the consumer.

        Args:
            rabbitmq_url: RabbitMQ connection URL.
            use_case: The ShowNotificationUseCase to delegate to.
            publisher: Publisher for sending answers.
            config: Application configuration.
        """
        self._rabbitmq_url = rabbitmq_url
        self._use_case = use_case
        self._publisher = publisher
        self._config = config
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None
        self._background_tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        """Start consuming messages from all three notification queues."""
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        # Declare all three queues
        queues_config = {
            "chappie.agent.results": {
                "ttl": 300000,
                "dlq": "chappie.agent.results.dlq",
            },
            "chappie.agent.questions": {
                "ttl": 600000,
                "dlq": "chappie.agent.questions.dlq",
            },
            "chappie.notifications": {
                "ttl": 120000,
                "dlq": "chappie.notifications.dlq",
            },
        }

        for queue_name, config_data in queues_config.items():
            queue = await self._channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-message-ttl": config_data["ttl"],
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": config_data["dlq"],
                },
            )
            await queue.consume(self._on_message)

        logger.info(
            "NotificationConsumer started, consuming: chappie.agent.results, "
            "chappie.agent.questions, chappie.notifications"
        )

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        """Route an incoming message to the appropriate handler.

        Args:
            message: The incoming RabbitMQ message.
        """
        async with message.process(ignore_processed=True):
            try:
                routing_key = message.routing_key
                body = message.body
                payload = json.loads(body)

                if routing_key == "chappie.agent.results":
                    await self._on_agent_result(payload)
                elif routing_key == "chappie.agent.questions":
                    task = asyncio.create_task(self._on_agent_question(payload))
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
                elif routing_key == "chappie.notifications":
                    await self._on_notification(payload)
                else:
                    logger.warning(
                        "Unknown routing key",
                        extra={"routing_key": routing_key},
                    )

            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in notification", extra={"error": str(e)})
                await message.nack(requeue=False)
            except Exception as e:
                logger.error(
                    "Unhandled error in NotificationConsumer",
                    extra={"error": str(e)},
                )
                await message.nack(requeue=False)

    async def _on_agent_result(self, payload: dict) -> None:
        """Handle an agent result message.

        Shows a fire-and-forget notification (no wait for response).

        Args:
            payload: The message payload.
        """
        agent = payload.get("agent", "unknown")
        status = payload.get("status", "success")
        result_text = payload.get("result", "")
        session_id = _parse_uuid(payload.get("session_id"))

        title = f"Agent {agent} completed"
        message = f"Status: {status}\n{result_text[:200]}"

        notification = NotificationMessage(
            timestamp=datetime.now(),
            title=title,
            message=message,
            urgency=NotificationUrgency.NORMAL,
            actions=[],
            category=NotificationCategory.AGENT_COMPLETE,
            session_id=session_id,
        )

        await self._use_case.execute(notification)
        logger.info(
            "Agent result notification shown",
            extra={"agent": agent, "status": status},
        )

    async def _on_agent_question(self, payload: dict) -> None:
        """Handle an agent question message.

        Shows a notification with actions and waits for user response.

        Args:
            payload: The message payload.
        """
        agent = payload.get("agent", "unknown")
        question = payload.get("question", "")
        options = payload.get("options", [])
        notification_id = payload.get("notification_id", "")
        session_id = _parse_uuid(payload.get("session_id"))

        actions = [
            NotificationAction(key=opt.get("key", ""), label=opt.get("label", ""))
            for opt in options
        ]

        notification = NotificationMessage(
            timestamp=datetime.now(),
            title=f"Chappie {agent} needs your input",
            message=question,
            urgency=NotificationUrgency.CRITICAL,
            actions=actions,
            category=NotificationCategory.QUESTION,
            session_id=session_id,
        )

        result = await self._use_case.execute(notification)

        # If user answered, the answer is already published by the use case
        if result.user_answer:
            logger.info(
                "Agent question answered",
                extra={"agent": agent, "answer": result.user_answer},
            )
        else:
            logger.info(
                "Agent question unanswered (timeout)",
                extra={"agent": agent},
            )

    async def _on_notification(self, payload: dict) -> None:
        """Handle a generic notification message.

        Shows a fire-and-forget notification (no wait).

        Args:
            payload: The message payload.
        """
        title = payload.get("title", "Chappie Notification")
        message = payload.get("message", "")
        urgency_str = payload.get("urgency", "normal")
        session_id = _parse_uuid(payload.get("session_id"))

        actions_data = payload.get("actions", [])
        actions = [
            NotificationAction(key=a.get("key", ""), label=a.get("label", ""))
            for a in actions_data
        ]

        notification = NotificationMessage(
            timestamp=datetime.now(),
            title=title,
            message=message,
            urgency=NotificationUrgency(urgency_str),
            actions=actions,
            category=NotificationCategory.INFO,
            session_id=session_id,
        )

        await self._use_case.execute(notification)
        logger.info(
            "Generic notification shown",
            extra={"title": title, "actions": len(actions)},
        )

    async def stop(self) -> None:
        """Stop the consumer and close connections."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("NotificationConsumer stopped")
