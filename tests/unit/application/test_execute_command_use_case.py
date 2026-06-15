"""Unit tests for ExecuteCommandUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from chappie_notification.application.dto.results import CommandExecutionResult
from chappie_notification.application.use_cases.execute_command import (
    ExecuteCommandUseCase,
)
from chappie_notification.domain.exceptions.domain_exceptions import (
    CommandNotAllowedError,
)
from chappie_notification.domain.models.enums import ExecutionStatus
from chappie_notification.domain.models.value_objects import TerminalCommand


@pytest.fixture
def use_case(
    mock_command_executor: AsyncMock,
    mock_command_validator: MagicMock,
    mock_rabbitmq_publisher: AsyncMock,
    test_config,
) -> ExecuteCommandUseCase:
    return ExecuteCommandUseCase(
        command_executor=mock_command_executor,
        command_validator=mock_command_validator,
        rabbitmq_publisher=mock_rabbitmq_publisher,
        config=test_config,
    )


class TestExecuteCommandUseCase:
    """Tests for ExecuteCommandUseCase."""

    @pytest.mark.asyncio
    async def test_should_execute_allowed_command(
        self,
        use_case: ExecuteCommandUseCase,
        mock_command_executor: AsyncMock,
        mock_command_validator: MagicMock,
        mock_rabbitmq_publisher: AsyncMock,
    ) -> None:
        mock_command_validator.is_allowed.return_value = True
        command = TerminalCommand(
            enabled=True,
            command="ls -la",
            requires_confirmation=False,
        )

        result = await use_case.execute(command, uuid4())
        assert result.success is True
        mock_command_executor.execute.assert_called_once_with(
            command="ls -la",
            timeout=30,
        )

    @pytest.mark.asyncio
    async def test_should_raise_error_on_disallowed_command(
        self,
        use_case: ExecuteCommandUseCase,
        mock_command_validator: MagicMock,
    ) -> None:
        mock_command_validator.is_allowed.return_value = False
        command = TerminalCommand(
            enabled=True,
            command="rm -rf /",
            requires_confirmation=False,
        )

        with pytest.raises(CommandNotAllowedError):
            await use_case.execute(command, uuid4())

    @pytest.mark.asyncio
    async def test_should_publish_error_on_failure(
        self,
        use_case: ExecuteCommandUseCase,
        mock_command_executor: AsyncMock,
        mock_command_validator: MagicMock,
        mock_rabbitmq_publisher: AsyncMock,
    ) -> None:
        mock_command_validator.is_allowed.return_value = True
        mock_command_executor.execute.return_value = CommandExecutionResult(
            success=False,
            stdout="",
            stderr="Command failed",
            exit_code=1,
        )
        command = TerminalCommand(
            enabled=True,
            command="invalid-command",
            requires_confirmation=False,
        )

        result = await use_case.execute(command, uuid4())
        assert result.success is False
        assert result.status == ExecutionStatus.FAILURE
