"""TTS synthesizer port definition."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TTSSynthesizerPort(Protocol):
    """Port for text-to-speech synthesis."""

    async def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Synthesize text to speech audio.

        Args:
            text: The text to synthesize.
            voice: The voice to use.
            output_path: Path where the audio file will be written.

        Returns:
            Path to the generated audio file.
        """
        ...
