"""Domain value objects for chappie-notification.

All classes are frozen dataclasses with no framework dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from chappie_notification.domain.models.enums import (
    ErrorType,
    ExecutionStatus,
    NotificationCategory,
    NotificationUrgency,
    TTSPriority,
)


@dataclass(frozen=True)
class ChappieResponse:
    """A processed response from the AI model that may include actions."""

    session_id: UUID
    timestamp: datetime
    voice_response: str
    agent_call: AgentCall | None = None
    terminal_command: TerminalCommand | None = None
    notification: NotificationRequest | None = None
    memory_update: MemoryUpdate | None = None


@dataclass(frozen=True)
class AgentCall:
    """Request to execute an agent."""

    enabled: bool
    agent: str
    prompt: str
    notify_on_complete: bool


@dataclass(frozen=True)
class TerminalCommand:
    """Request to execute a terminal command."""

    enabled: bool
    command: str
    requires_confirmation: bool


@dataclass(frozen=True)
class NotificationRequest:
    """Request to show a notification."""

    enabled: bool
    title: str
    message: str
    urgency: NotificationUrgency


@dataclass(frozen=True)
class MemoryUpdate:
    """Request to update memory."""

    save_to_memory: bool
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TTSRequest:
    """Request to generate TTS audio."""

    session_id: UUID
    timestamp: datetime
    text: str
    priority: TTSPriority
    ducking: bool
    show_text: bool


@dataclass(frozen=True)
class AgentResult:
    """Result of an agent execution."""

    session_id: UUID
    timestamp: datetime
    agent: str
    status: ExecutionStatus
    result: str
    notify_user: bool


@dataclass(frozen=True)
class AgentQuestion:
    """Question from an agent requiring user interaction."""

    session_id: UUID
    timestamp: datetime
    agent: str
    question: str
    options: list[QuestionOption]
    notification_id: UUID


@dataclass(frozen=True)
class QuestionOption:
    """An option in an agent question."""

    key: str
    label: str


@dataclass(frozen=True)
class AgentAnswer:
    """User's answer to an agent question."""

    notification_id: UUID
    session_id: UUID
    timestamp: datetime
    answer: str


@dataclass(frozen=True)
class ErrorMessage:
    """Error message for execution errors."""

    session_id: UUID
    timestamp: datetime
    original_request: str
    error_type: ErrorType
    error: str
    context: ErrorContext | None = None


@dataclass(frozen=True)
class ErrorContext:
    """Contextual information about an error."""

    agent: str | None = None
    command: str | None = None


@dataclass(frozen=True)
class NotificationMessage:
    """Message for displaying a notification."""

    timestamp: datetime
    title: str
    message: str
    urgency: NotificationUrgency
    actions: list[NotificationAction]
    category: NotificationCategory
    session_id: UUID | None = None


@dataclass(frozen=True)
class NotificationAction:
    """An action option in a notification."""

    key: str
    label: str
