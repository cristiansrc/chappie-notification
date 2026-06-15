"""Integration tests for OpenCodeAgentExecutorAdapter.

These tests verify the adapter logic using mocked subprocess execution.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from chappie_notification.infrastructure.adapters.opencode_agent_adapter import (
    OpenCodeAgentExecutorAdapter,
)


@pytest.mark.asyncio
class TestOpenCodeAgentExecutorAdapter:
    """Integration tests for OpenCodeAgentExecutorAdapter."""

    async def test_should_parse_successful_execution(self) -> None:
        """Test that a successful subprocess execution returns correct result."""
        adapter = OpenCodeAgentExecutorAdapter(timeout=120)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Task completed", b"")
            mock_subprocess.return_value = mock_process

            result = await adapter.execute(agent="dev", prompt="run tests")

            assert result.success is True
            assert result.stdout == "Task completed"
            assert result.stderr == ""
            assert result.exit_code == 0

    async def test_should_handle_timeout(self) -> None:
        """Test that a timeout raises TimeoutError and returns failure."""
        adapter = OpenCodeAgentExecutorAdapter(timeout=120)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = TimeoutError
            mock_subprocess.return_value = mock_process

            result = await adapter.execute(agent="dev", prompt="run tests")

            assert result.success is False
            assert result.stderr == "timeout"
