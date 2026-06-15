"""Async file writer adapter using aiofiles."""

from __future__ import annotations

import logging
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)


class AsyncFileWriterAdapter:
    """Writes files asynchronously using aiofiles."""

    async def write(self, path: str, content: str) -> None:
        """Write content to a file.

        Creates parent directories if they don't exist.

        Args:
            path: Path to the file to write.
            content: Content to write.

        Raises:
            IOError: If the file cannot be written.
        """
        file_path = Path(path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug("Writing file", extra={"path": path, "size": len(content)})

        async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
            await f.write(content)

        logger.info("File written successfully", extra={"path": path})
