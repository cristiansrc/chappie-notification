"""Edge-TTS synthesizer adapter."""

from __future__ import annotations

import asyncio
import logging

from chappie_notification.domain.exceptions.domain_exceptions import TTSGenerationError

logger = logging.getLogger(__name__)


class EdgeTTSSynthesizerAdapter:
    """Generates TTS audio using Microsoft Edge-TTS."""

    def __init__(self, voice: str = "es-AR-ElenaNeural") -> None:
        """Initialize the adapter.

        Args:
            voice: Default voice for TTS synthesis.
        """
        self._default_voice = voice

    async def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Synthesize text to speech audio.

        Uses edge-tts library to generate MP3 audio file.
        Retries up to 2 times on failure.

        Args:
            text: The text to synthesize.
            voice: The voice to use.
            output_path: Path where the audio file will be written.

        Returns:
            Path to the generated audio file.

        Raises:
            TTSGenerationError: If synthesis fails after all retries.
        """
        voice_to_use = voice or self._default_voice
        max_retries = 2
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                import edge_tts

                communicate = edge_tts.Communicate(text=text, voice=voice_to_use)
                await communicate.save(output_path)
                logger.info(
                    "TTS audio saved to %s",
                    output_path,
                    extra={"voice": voice_to_use, "text_length": len(text)},
                )
                return output_path

            except Exception as e:
                last_error = e
                logger.warning(
                    "Edge-TTS synthesis failed (attempt %d/%d)",
                    attempt + 1,
                    max_retries + 1,
                    extra={"error": str(e)},
                )
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s

        error_msg = f"TTS synthesis failed after {max_retries + 1} attempts: {last_error}"
        logger.error(error_msg)
        raise TTSGenerationError(error_msg)
