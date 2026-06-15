"""Notification sender port definition."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class NotificationSenderPort(Protocol):
    """Port for sending and interacting with system notifications."""

    async def send(self, title: str, message: str, urgency: str, actions: list[dict]) -> str | None:
        """Send a notification.

        Args:
            title: Notification title.
            message: Notification message body.
            urgency: Urgency level (low, normal, critical).
            actions: List of action dicts with 'key' and 'label'.

        Returns:
            Notification ID if actions are present, None otherwise.
            Returns immediately without blocking the event loop.
        """
        ...

    async def wait_for_action(self, notification_id: str, timeout_seconds: int) -> str | None:
        """Wait for a user action on a notification.

        Uses D-Bus signals from SwayNC to capture the selected action.

        Args:
            notification_id: ID of the notification to wait for.
            timeout_seconds: Maximum time to wait in seconds.

        Returns:
            Key of the selected action, or None on timeout.
        """
        ...
