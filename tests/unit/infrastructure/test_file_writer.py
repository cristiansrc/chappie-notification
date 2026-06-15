"""Unit tests for AsyncFileWriterAdapter."""

import tempfile
from pathlib import Path

import pytest

from chappie_notification.infrastructure.adapters.async_file_writer_adapter import (
    AsyncFileWriterAdapter,
)


class TestAsyncFileWriterAdapter:
    """Tests for AsyncFileWriterAdapter."""

    @pytest.mark.asyncio
    async def test_should_write_file(self) -> None:
        writer = AsyncFileWriterAdapter()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            await writer.write(str(filepath), "Hello World")
            assert filepath.exists()
            assert filepath.read_text() == "Hello World"

    @pytest.mark.asyncio
    async def test_should_create_parent_directories(self) -> None:
        writer = AsyncFileWriterAdapter()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "nested" / "test.txt"
            await writer.write(str(filepath), "Nested content")
            assert filepath.exists()
            assert filepath.read_text() == "Nested content"

    @pytest.mark.asyncio
    async def test_should_write_empty_content(self) -> None:
        writer = AsyncFileWriterAdapter()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.txt"
            await writer.write(str(filepath), "")
            assert filepath.exists()
            assert filepath.read_text() == ""
