"""Integration tests for HTTPXClientAdapter using pytest-httpx."""

from __future__ import annotations

import pytest
import httpx

from chappie_notification.infrastructure.adapters.httpx_client_adapter import (
    HTTPXClientAdapter,
)


@pytest.mark.asyncio
class TestHTTPXClientAdapter:
    """Integration tests for HTTPXClientAdapter using mocked HTTP responses."""

    async def test_should_post_json(self, httpx_mock) -> None:
        """Test POST request with JSON body returns parsed response."""
        httpx_mock.add_response(
            url="http://localhost:8765/play-tts",
            method="POST",
            json={"status": "completed"},
        )

        adapter = HTTPXClientAdapter()
        result = await adapter.post(
            url="http://localhost:8765/play-tts",
            json={"audio_file": "/tmp/test.mp3", "text": "hello", "ducking": True},
        )
        assert result == {"status": "completed"}

    async def test_should_handle_timeout(self, httpx_mock) -> None:
        """Test timeout raises an HTTPError."""
        httpx_mock.add_exception(
            httpx.TimeoutException("Request timed out"),
            url="http://localhost:8765/play-tts",
        )

        adapter = HTTPXClientAdapter()
        with pytest.raises(httpx.TimeoutException):
            await adapter.post(
                url="http://localhost:8765/play-tts",
                json={"audio_file": "/tmp/test.mp3", "text": "hello", "ducking": True},
                timeout=1,
            )

    async def test_should_handle_connection_error(self, httpx_mock) -> None:
        """Test connection error raises an HTTPError."""
        httpx_mock.add_exception(
            httpx.ConnectError("Connection refused"),
            url="http://localhost:9999/test",
        )

        adapter = HTTPXClientAdapter()
        with pytest.raises(httpx.ConnectError):
            await adapter.post(
                url="http://localhost:9999/test",
                json={"data": "test"},
                timeout=1,
            )

    async def test_should_send_custom_headers(self, httpx_mock) -> None:
        """Test that custom headers are sent with the request."""
        httpx_mock.add_response(
            url="http://localhost:5678/webhook/test",
            method="POST",
            json={"status": "accepted"},
        )

        adapter = HTTPXClientAdapter()
        result = await adapter.post(
            url="http://localhost:5678/webhook/test",
            json={"data": "test"},
            headers={"X-Webhook-Secret": "mysecret"},
        )
        assert result == {"status": "accepted"}
