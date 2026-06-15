"""Unit tests for ExecuteAgentUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chappie_notification.application.dto.results import AgentExecutionResult
from chappie_notification.application.use_cases.execute_agent import ExecuteAgentUseCase
from chappie_notification.domain.models.enums import ExecutionStatus
from chappie_notification.domain.models.value_objects import AgentCall


@pytest.fixture
def use_case(
    mock_agent_executor: AsyncMock,
    mock_rabbitmq_publisher: AsyncMock,
    test_config,
) -> ExecuteAgentUseCase:
    return ExecuteAgentUseCase(
        agent_executor=mock_agent_executor,
        rabbitmq_publisher=mock_rabbitmq_publisher,
        config=test_config,
    )


class TestExecuteAgentUseCase:
    """Tests for ExecuteAgentUseCase."""

    @pytest.mark.asyncio
    async def test_should_execute_agent_and_publish_result(
        self,
        use_case: ExecuteAgentUseCase,
        mock_agent_executor: AsyncMock,
        mock_rabbitmq_publisher: AsyncMock,
    ) -> None:
        agent_call = AgentCall(
            enabled=True,
            agent="dev",
            prompt="run tests",
            notify_on_complete=True,
        )
        session_id = uuid4()

        result = await use_case.execute(agent_call, session_id)
        assert result.success is True
        assert result.status == ExecutionStatus.SUCCESS
        mock_agent_executor.execute.assert_called_once_with(
            agent="dev",
            prompt="run tests",
            timeout=120,
        )
        # Should publish to chappie.agent.results
        publish_calls = mock_rabbitmq_publisher.publish.call_args_list
        assert any(
            call.kwargs.get("queue") == "chappie.agent.results"
            for call in publish_calls
        )

    @pytest.mark.asyncio
    async def test_should_publish_error_on_failure(
        self,
        use_case: ExecuteAgentUseCase,
        mock_agent_executor: AsyncMock,
        mock_rabbitmq_publisher: AsyncMock,
    ) -> None:
        mock_agent_executor.execute.return_value = AgentExecutionResult(
            success=False,
            stdout="",
            stderr="Agent crashed",
            exit_code=1,
        )
        agent_call = AgentCall(
            enabled=True,
            agent="dev",
            prompt="run",
            notify_on_complete=False,
        )
        result = await use_case.execute(agent_call, uuid4())
        assert result.success is False
        assert result.status == ExecutionStatus.FAILURE

        # Should publish to chappie.errors
        publish_calls = mock_rabbitmq_publisher.publish.call_args_list
        error_calls = [
            call
            for call in publish_calls
            if call.kwargs.get("queue") == "chappie.errors"
        ]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_should_handle_exception_gracefully(
        self,
        use_case: ExecuteAgentUseCase,
        mock_agent_executor: AsyncMock,
    ) -> None:
        mock_agent_executor.execute.side_effect = Exception("Unexpected error")
        agent_call = AgentCall(
            enabled=True,
            agent="dev",
            prompt="run",
            notify_on_complete=False,
        )
        result = await use_case.execute(agent_call, uuid4())
        assert result.success is False
        assert result.status == ExecutionStatus.FAILURE
        assert result.error is not None
