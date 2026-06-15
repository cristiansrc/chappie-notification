"""Application DTOs (Result objects) for chappie-notification.

These are data containers that cross the boundary between use cases and consumers.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from chappie_notification.domain.models.enums import ExecutionStatus


@dataclass(frozen=True)
class ProcessResponseResult:
    """Result of processing a ChappieResponse."""

    success: bool
    tts_requested: bool = False
    agent_started: bool = False
    command_started: bool = False
    error: str | None = None


@dataclass(frozen=True)
class HandleErrorResult:
    """Result of handling an error."""

    success: bool
    n8n_notified: bool = False
    error: str | None = None


@dataclass(frozen=True)
class GenerateTTSResult:
    """Result of generating TTS audio."""

    success: bool
    audio_path: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ShowNotificationResult:
    """Result of showing a notification."""

    success: bool
    notification_id: str | None = None
    user_answer: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ExecuteAgentResult:
    """Result of executing an agent."""

    success: bool
    status: ExecutionStatus
    result: str
    error: str | None = None


@dataclass(frozen=True)
class CommandExecutionResult:
    """Result of executing a shell command."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int


@dataclass(frozen=True)
class AgentExecutionResult:
    """Raw result from the agent executor (subprocess)."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
