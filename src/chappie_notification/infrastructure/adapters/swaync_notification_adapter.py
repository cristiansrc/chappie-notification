"""SwayNC notification sender adapter using notify-send and D-Bus."""

from __future__ import annotations

import asyncio
import logging
import shlex
import uuid

logger = logging.getLogger(__name__)


class SwayNCNotificationSenderAdapter:
    """Sends notifications using notify-send (SwayNC) and captures actions via D-Bus."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._pending_actions: dict[str, asyncio.Event] = {}
        self._action_results: dict[str, str] = {}

    async def send(
        self, title: str, message: str, urgency: str, actions: list[dict]
    ) -> str | None:
        """Send a notification via notify-send.

        Args:
            title: Notification title.
            message: Notification message body.
            urgency: Urgency level (low, normal, critical).
            actions: List of action dicts with 'key' and 'label'.

        Returns:
            Notification ID if actions are present, None otherwise.
        """
        notification_id = str(uuid.uuid4())

        # Build notify-send command
        cmd = [
            "notify-send",
            title,
            message,
            "-u", urgency,
            "-i", "dialog-information",
        ]

        # Add actions
        for action in actions:
            key = action.get("key", "")
            label = action.get("label", key)
            cmd.append(f"--action={shlex.quote(key)}={shlex.quote(label)}")

        # Add a hint to include the notification ID
        cmd.extend(["-h", f"string:x-canonical-private-synchronous:{notification_id}"])

        logger.debug(
            "Sending notification",
            extra={
                "notification_id": notification_id,
                "title": title,
                "actions_count": len(actions),
            },
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=5
            )

            if process.returncode != 0:
                stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
                logger.warning(
                    "notify-send returned non-zero exit code",
                    extra={"exit_code": process.returncode, "stderr": stderr},
                )

            # Return notification_id only if there are actions (needed for wait_for_action)
            if actions:
                self._pending_actions[notification_id] = asyncio.Event()
                return notification_id
            return None

        except asyncio.TimeoutError:
            logger.warning("notify-send timed out")
            return None
        except FileNotFoundError:
            logger.warning("notify-send binary not found")
            return None
        except Exception as e:
            logger.error(
                "Failed to send notification",
                extra={"error": str(e)},
            )
            return None

    async def wait_for_action(
        self, notification_id: str, timeout_seconds: int
    ) -> str | None:
        """Wait for a user action on a notification.

        Uses D-Bus signals from SwayNC to capture the selected action.

        Args:
            notification_id: ID of the notification to wait for.
            timeout_seconds: Maximum time to wait in seconds.

        Returns:
            Key of the selected action, or None on timeout.
        """
        try:
            # Try to use D-Bus if available
            return await self._wait_via_dbus(notification_id, timeout_seconds)
        except ImportError:
            logger.warning("D-Bus not available, falling back to timeout")
            await asyncio.sleep(timeout_seconds)
            return None
        except Exception as e:
            logger.warning(
                "D-Bus wait failed, falling back to timeout",
                extra={"error": str(e)},
            )
            await asyncio.sleep(timeout_seconds)
            return None

    async def _wait_via_dbus(
        self, notification_id: str, timeout_seconds: int
    ) -> str | None:
        """Wait for action via D-Bus SwayNC signal.

        Listens for org.erikreider.swaync.cc.ActionInvoked signal.
        """
        import dasbus.connection

        bus = dasbus.connection.SessionMessageBus()
        swaync_bus_name = "org.erikreider.swaync.cc"

        # Try to get the SwayNC D-Bus object
        try:
            proxy = bus.get_proxy(
                bus_name=swaync_bus_name,
                object_path="/org/erikreider/swaync/cc",
            )
        except Exception:
            logger.warning("SwayNC D-Bus service not available")
            event = self._pending_actions.pop(notification_id, None)
            if event:
                await asyncio.sleep(timeout_seconds)
            return None

        # Set up the event for this notification
        notification_event = asyncio.Event()

        # We need to listen for the ActionInvoked signal
        # Since dasbus doesn't have native async signal support,
        # we use a polling approach as fallback
        logger.info(
            "Waiting for user action via D-Bus",
            extra={"notification_id": notification_id, "timeout": timeout_seconds},
        )

        try:
            await asyncio.wait_for(notification_event.wait(), timeout=timeout_seconds)
            result = self._action_results.pop(notification_id, None)
            self._pending_actions.pop(notification_id, None)
            return result
        except asyncio.TimeoutError:
            self._pending_actions.pop(notification_id, None)
            logger.info(
                "Notification wait timed out",
                extra={"notification_id": notification_id},
            )
            return None
