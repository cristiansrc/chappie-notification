"""Unit tests for HandleErrorUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chappie_notification.application.use_cases.handle_error import HandleErrorUseCase
from chappie_notification.domain.models.enums import ErrorType
from chappie_notification.domain.models.value_objects import ErrorMessage


@pytest.fixture
def use_case(
    mock_http_client: AsyncMock, test_config
) -> HandleErrorUseCase:
    return HandleErrorUseCase(
        http_client=mock_http_client,
        config=test_config,
    )


class TestHandleErrorUseCase:
    """Tests for HandleErrorUseCase."""

    @pytest.mark.asyncio
    async def test_should_notify_n8n_on_error(
        self, use_case: HandleErrorUseCase, mock_http_client: AsyncMock
    ) -> None:
        error = ErrorMessage(
            session_id=uuid4(),
            timestamp=datetime.now(),
            original_request="test request",
            error_type=ErrorType.AGENT_FAILURE,
            error="Agent crashed",
        )
        result = await use_case.execute(error)
        assert result.success is True
        assert result.n8n_notified is True
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_retry_on_failure(
        self, use_case: HandleErrorUseCase, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.side_effect = [
            ConnectionError("First fail"),
            {"status": "accepted"},
        ]
        error = ErrorMessage(
            session_id=uuid4(),
            timestamp=datetime.now(),
            original_request="test",
            error_type=ErrorType.COMMAND_FAILURE,
            error="Command failed",
        )
        result = await use_case.execute(error)
        assert result.success is True
        assert result.n8n_notified is True
        assert mock_http_client.post.call_count == 2
