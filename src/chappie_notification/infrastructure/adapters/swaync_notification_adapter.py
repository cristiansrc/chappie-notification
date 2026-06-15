"""SwayNC notification sender adapter using notify-send and D-Bus."""

from __future__ import annotations

import asyncio
import logging
import shlex
import uuid

from dbus_next import BusType, Message, MessageType
from dbus_next.aio import MessageBus

logger = logging.getLogger(__name__)


class SwayNCNotificationSenderAdapter:
    """Sends notifications using notify-send (SwayNC) and captures actions via D-Bus."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._pending_actions: dict[str, asyncio.Event] = {}
        self._action_results: dict[str, str] = {}
        self._dbus_connection: MessageBus | None = None
        self._dbus_connected: bool = False

    async def _ensure_dbus_connection(self) -> MessageBus | None:
        """Ensure D-Bus session connection is established and listening for signals.

        Connects to the SESSION bus via dbus-next and subscribes to the
        ``org.erikreider.swaync.cc.ActionInvoked`` signal.

        Returns:
            The connected MessageBus instance, or None if connection failed.
        """
        if self._dbus_connected and self._dbus_connection is not None:
            return self._dbus_connection

        try:
            bus = await MessageBus(bus_type=BusType.SESSION).connect()

            # Register signal handler for ActionInvoked
            async def on_message(msg: Message) -> None:
                if msg.message_type == MessageType.SIGNAL:
                    await self._on_action_invoked(msg)

            bus.on_message = on_message

            # Subscribe to ActionInvoked signal from SwayNC
            await bus.call(
                Message(
                    destination="org.freedesktop.DBus",
                    path="/org/freedesktop/DBus",
                    interface="org.freedesktop.DBus",
                    member="AddMatch",
                    signature="s",
                    body=[
                        "interface='org.erikreider.swaync.cc',"
                        "member='ActionInvoked'"
                    ],
                )
            )

            self._dbus_connection = bus
            self._dbus_connected = True
            logger.info("Connected to D-Bus session bus and listening for signals")
            return bus

        except Exception as e:
            logger.warning(
                "Failed to connect to D-Bus session bus",
                extra={"error": str(e)},
            )
            self._dbus_connected = False
            self._dbus_connection = None
            return None

    async def _on_action_invoked(self, msg: Message) -> None:
        """Handle ActionInvoked signal from SwayNC.

        Signal signature from SwayNC: ``(uint32 id, string action_key)``.
        Sets the corresponding :class:`asyncio.Event` so that
        :meth:`_wait_via_dbus` can resume.

        Args:
            msg: The incoming D-Bus signal message.
        """
        try:
            if not msg.body or len(msg.body) < 2:
                return

            notification_id = str(msg.body[0])
            action_key = str(msg.body[1])

            self._action_results[notification_id] = action_key
            event = self._pending_actions.get(notification_id)
            if event is not None:
                event.set()

            logger.debug(
                "Action invoked via D-Bus",
                extra={
                    "notification_id": notification_id,
                    "action_key": action_key,
                },
            )
        except Exception as e:
            logger.error(
                "Error handling D-Bus ActionInvoked signal",
                extra={"error": str(e)},
            )

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
        local_id = str(uuid.uuid4())

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

        # Print the server-assigned notification ID to stdout
        cmd.append("--print-id")

        # Add a hint for notification replacement/deduplication
        cmd.extend(["-h", f"string:x-canonical-private-synchronous:{local_id}"])

        logger.debug(
            "Sending notification",
            extra={
                "local_id": local_id,
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

            # Parse server-assigned notification ID from --print-id
            server_id = ""
            if stdout_bytes:
                server_id = stdout_bytes.decode("utf-8", errors="replace").strip()

            # Use server ID if available, otherwise fall back to local ID
            notification_id = server_id if server_id else local_id

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

        Uses dbus-next async signal listener connected via
        :meth:`_ensure_dbus_connection`. The ``ActionInvoked`` signal is
        handled by :meth:`_on_action_invoked` which sets the corresponding
        :class:`asyncio.Event`.

        Args:
            notification_id: ID of the notification to wait for.
            timeout_seconds: Maximum time to wait in seconds.

        Returns:
            Key of the selected action, or None on timeout.
        """
        # Ensure D-Bus connection and signal listener are active
        bus = await self._ensure_dbus_connection()
        if bus is None:
            logger.warning(
                "SwayNC D-Bus service not available, falling back to timeout",
                extra={"notification_id": notification_id},
            )
            self._pending_actions.pop(notification_id, None)
            await asyncio.sleep(timeout_seconds)
            return None

        # Get or create the event for this notification
        notification_event = self._pending_actions.get(notification_id)
        if notification_event is None:
            notification_event = asyncio.Event()
            self._pending_actions[notification_id] = notification_event

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
