"""HandleErrorUseCase implementation.

Handles execution errors by notifying n8n via webhook for error recovery.
"""

from __future__ import annotations

import asyncio
import logging

from chappie_notification.application.dto.results import HandleErrorResult
from chappie_notification.application.ports.http_port import HTTPClientPort
from chappie_notification.domain.models.value_objects import ErrorMessage
from chappie_notification.infrastructure.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class HandleErrorUseCase:
    """Handles execution errors by delegating to n8n for error recovery."""

    def __init__(self, http_client: HTTPClientPort, config: AppConfig) -> None:
        """Initialize the use case.

        Args:
            http_client: Port for HTTP requests.
            config: Application configuration.
        """
        self._http_client = http_client
        self._config = config

    async def execute(self, error: ErrorMessage) -> HandleErrorResult:
        """Handle an error by notifying n8n.

        Does NOT reproduce the original voice. n8n will generate a new
        response and publish to chappie.tts.requests.

        Args:
            error: The error message to handle.

        Returns:
            HandleErrorResult indicating success or failure.
        """
        session_id = str(error.session_id)
        logger.info(
            "Handling error",
            extra={
                "session_id": session_id,
                "error_type": error.error_type.value,
                "error": error.error,
            },
        )

        # Build n8n webhook payload
        payload = {
            "original_request": error.original_request,
            "error": error.error,
            "context": str(error.context) if error.context else "",
            "session_id": session_id,
        }

        webhook_url = f"{self._config.n8n_base_url}/webhook/chappie-error-handler"
        headers = {"X-Webhook-Secret": self._config.n8n_webhook_secret}

        # Retry logic: 2 attempts with exponential backoff (1s, 2s)
        max_retries = 2
        last_error: str | None = None

        for attempt in range(max_retries + 1):
            try:
                response = await self._http_client.post(
                    url=webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self._config.http_timeout,
                )
                logger.info(
                    "n8n webhook called successfully",
                    extra={"session_id": session_id, "response": response},
                )
                return HandleErrorResult(success=True, n8n_notified=True)

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "n8n webhook call failed",
                    extra={
                        "session_id": session_id,
                        "attempt": attempt + 1,
                        "error": last_error,
                    },
                )
                if attempt < max_retries:
                    backoff = 2 ** attempt  # 1s, 2s
                    await asyncio.sleep(backoff)

        logger.error(
            "Failed to notify n8n after all retries",
            extra={"session_id": session_id, "error": last_error},
        )
        return HandleErrorResult(
            success=False,
            n8n_notified=False,
            error=last_error,
        )
