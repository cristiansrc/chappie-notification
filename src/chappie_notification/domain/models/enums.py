"""Domain enums for chappie-notification."""

from enum import Enum


class TTSPriority(str, Enum):
    """Priority level for TTS requests."""

    NORMAL = "normal"
    HIGH = "high"


class ExecutionStatus(str, Enum):
    """Status of an execution (agent or command)."""

    SUCCESS = "success"
    FAILURE = "failure"


class ErrorType(str, Enum):
    """Type of error that occurred."""

    AGENT_FAILURE = "agent_failure"
    COMMAND_FAILURE = "command_failure"
    VALIDATION_ERROR = "validation_error"


class NotificationUrgency(str, Enum):
    """Urgency level for notifications."""

    LOW = "low"
    NORMAL = "normal"
    CRITICAL = "critical"


class NotificationCategory(str, Enum):
    """Category of notification."""

    AGENT_COMPLETE = "agent_complete"
    ERROR = "error"
    INFO = "info"
    QUESTION = "question"
