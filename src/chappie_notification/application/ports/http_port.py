"""HTTP client port definition."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class HTTPClientPort(Protocol):
    """Port for making HTTP requests."""

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
        """
        ...
