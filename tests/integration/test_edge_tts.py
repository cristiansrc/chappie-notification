"""Integration tests for EdgeTTSSynthesizerAdapter.

These tests verify the adapter logic using mocked edge-tts.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from chappie_notification.infrastructure.adapters.edge_tts_adapter import (
    EdgeTTSSynthesizerAdapter,
)


@pytest.mark.asyncio
class TestEdgeTTSSynthesizerAdapter:
    """Integration tests for EdgeTTSSynthesizerAdapter."""

    async def test_should_generate_audio(self) -> None:
        """Test generating TTS audio from text using mocked edge-tts."""
        adapter = EdgeTTSSynthesizerAdapter(voice="es-AR-ElenaNeural")

        with patch("edge_tts.Communicate") as mock_communicate:
            mock_instance = AsyncMock()
            mock_communicate.return_value = mock_instance
            mock_instance.save = AsyncMock()

            result = await adapter.synthesize(
                text="Hola mundo",
                voice="es-AR-ElenaNeural",
                output_path="/tmp/test_chappie_tts.mp3",
            )

            assert result == "/tmp/test_chappie_tts.mp3"
            mock_communicate.assert_called_once_with(text="Hola mundo", voice="es-AR-ElenaNeural")
            mock_instance.save.assert_called_once_with("/tmp/test_chappie_tts.mp3")

    async def test_should_use_custom_voice(self) -> None:
        """Test using a custom voice for TTS."""
        adapter = EdgeTTSSynthesizerAdapter(voice="en-US-JennyNeural")

        with patch("edge_tts.Communicate") as mock_communicate:
            mock_instance = AsyncMock()
            mock_communicate.return_value = mock_instance
            mock_instance.save = AsyncMock()

            result = await adapter.synthesize(
                text="Hello world",
                voice="en-US-JennyNeural",
                output_path="/tmp/test_chappie_tts_en.mp3",
            )

            assert result == "/tmp/test_chappie_tts_en.mp3"
            mock_communicate.assert_called_once_with(text="Hello world", voice="en-US-JennyNeural")
