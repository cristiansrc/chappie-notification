"""GenerateTTSUseCase implementation.

Generates TTS audio and sends it to chappie-daemon for playback.
"""

from __future__ import annotations

import asyncio
import logging

from chappie_notification.application.dto.results import GenerateTTSResult
from chappie_notification.application.ports.file_writer_port import FileWriterPort
from chappie_notification.application.ports.http_port import HTTPClientPort
from chappie_notification.application.ports.tts_port import TTSSynthesizerPort
from chappie_notification.domain.models.value_objects import TTSRequest
from chappie_notification.infrastructure.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class GenerateTTSUseCase:
    """Generates TTS audio and sends it to chappie-daemon for playback."""

    def __init__(
        self,
        tts_synthesizer: TTSSynthesizerPort,
        file_writer: FileWriterPort,
        http_client: HTTPClientPort,
        config: AppConfig,
    ) -> None:
        """Initialize the use case.

        Args:
            tts_synthesizer: Port for TTS synthesis.
            file_writer: Port for writing files.
            http_client: Port for HTTP requests.
            config: Application configuration.
        """
        self._tts_synthesizer = tts_synthesizer
        self._file_writer = file_writer
        self._http_client = http_client
        self._config = config

    async def execute(self, request: TTSRequest) -> GenerateTTSResult:
        """Generate TTS audio and send it to chappie-daemon.

        Steps:
        1. Generate audio with TTS engine.
        2. Write text to /tmp/chappie_tts_text.txt.
        3. Send POST /play-tts to chappie-daemon (fire-and-forget).

        Args:
            request: The TTS request to process.

        Returns:
            GenerateTTSResult with the result of the operation.
        """
        session_id = str(request.session_id)
        logger.info(
            "Generating TTS",
            extra={
                "session_id": session_id,
                "text_length": len(request.text),
                "priority": request.priority.value,
            },
        )

        # Step 1: Generate audio with TTS
        audio_path: str | None = None
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                audio_path = await self._tts_synthesizer.synthesize(
                    text=request.text,
                    voice=self._config.tts_voice,
                    output_path=self._config.tts_output_path,
                )
                logger.info(
                    "TTS audio generated",
                    extra={"session_id": session_id, "audio_path": audio_path},
                )
                break
            except Exception as e:
                logger.warning(
                    "TTS synthesis failed",
                    extra={
                        "session_id": session_id,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                )
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s
                else:
                    logger.error(
                        "TTS synthesis failed after all retries",
                        extra={"session_id": session_id, "error": str(e)},
                    )
                    return GenerateTTSResult(success=False, error=str(e))

        # Step 2: Write text file (best-effort)
        try:
            if request.show_text:
                await self._file_writer.write(
                    path=self._config.tts_text_path,
                    content=request.text,
                )
                logger.info(
                    "TTS text file written",
                    extra={"session_id": session_id},
                )
        except Exception as e:
            logger.warning(
                "Failed to write TTS text file",
                extra={"session_id": session_id, "error": str(e)},
            )

        # Step 3: Fire-and-forget POST to chappie-daemon
        try:
            daemon_payload = {
                "audio_file": audio_path or self._config.tts_output_path,
                "text": request.text,
                "ducking": request.ducking,
            }
            await self._http_client.post(
                url=f"{self._config.daemon_base_url}/play-tts",
                json=daemon_payload,
                timeout=5,
            )
            logger.info(
                "TTS playback requested from daemon",
                extra={"session_id": session_id},
            )
        except Exception as e:
            logger.warning(
                "Failed to notify daemon for TTS playback (fire-and-forget)",
                extra={"session_id": session_id, "error": str(e)},
            )

        return GenerateTTSResult(
            success=True,
            audio_path=audio_path or self._config.tts_output_path,
        )
