"""HTTPX client adapter."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class HTTPXClientAdapter:
    """HTTP client using httpx with timeout support."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._client = httpx.AsyncClient()

    async def post(
        self, url: str, json: dict, headers: dict | None = None, timeout: int = 10
    ) -> dict:
        """Make an HTTP POST request.

        Args:
            url: The URL to POST to.
            json: The JSON body of the request.
            headers: Optional HTTP headers.
            timeout: Request timeout in seconds.

        Returns:
            Response JSON as a dict.

        Raises:
            httpx.HTTPError: On HTTP errors or connection issues.
        """
        request_headers = headers or {}
        request_headers.setdefault("Content-Type", "application/json")

        logger.debug(
            "HTTP POST",
            extra={"url": url, "timeout": timeout},
        )

        response = await self._client.post(
            url,
            json=json,
            headers=request_headers,
            timeout=httpx.Timeout(timeout),
        )

        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
