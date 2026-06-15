"""Domain events for chappie-notification.

These represent business facts that have already occurred.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from chappie_notification.domain.models.enums import ExecutionStatus, TTSPriority


@dataclass(frozen=True)
class AgentExecutionStarted:
    """Emitted when an agent execution has started."""

    session_id: UUID
    agent: str
    timestamp: datetime


@dataclass(frozen=True)
class AgentExecutionCompleted:
    """Emitted when an agent execution has completed."""

    session_id: UUID
    agent: str
    status: ExecutionStatus
    result: str
    timestamp: datetime


@dataclass(frozen=True)
class TTSGenerationRequested:
    """Emitted when TTS generation has been requested."""

    session_id: UUID
    text: str
    priority: TTSPriority
    timestamp: datetime
