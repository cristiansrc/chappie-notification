"""Domain exceptions for chappie-notification."""


class CommandNotAllowedError(Exception):
    """Raised when a terminal command is not allowed by the whitelist."""

    pass


class AgentExecutionError(Exception):
    """Raised when an error occurs during agent execution."""

    pass


class TTSGenerationError(Exception):
    """Raised when an error occurs during TTS audio generation."""

    pass


class NotificationError(Exception):
    """Raised when an error occurs creating or sending a notification."""

    pass
