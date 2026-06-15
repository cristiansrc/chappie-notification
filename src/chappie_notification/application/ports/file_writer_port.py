"""File writer port definition."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class FileWriterPort(Protocol):
    """Port for writing files asynchronously."""

    async def write(self, path: str, content: str) -> None:
        """Write content to a file.

        Args:
            path: Path to the file to write.
            content: Content to write.
        """
        ...
