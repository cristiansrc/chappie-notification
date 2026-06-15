"""Unit tests for GenerateTTSUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chappie_notification.application.use_cases.generate_tts import GenerateTTSUseCase
from chappie_notification.domain.models.enums import TTSPriority
from chappie_notification.domain.models.value_objects import TTSRequest


@pytest.fixture
def use_case(
    mock_tts_synthesizer: AsyncMock,
    mock_file_writer: AsyncMock,
    mock_http_client: AsyncMock,
    test_config,
) -> GenerateTTSUseCase:
    return GenerateTTSUseCase(
        tts_synthesizer=mock_tts_synthesizer,
        file_writer=mock_file_writer,
        http_client=mock_http_client,
        config=test_config,
    )


class TestGenerateTTSUseCase:
    """Tests for GenerateTTSUseCase."""

    @pytest.mark.asyncio
    async def test_should_generate_tts_successfully(
        self, use_case: GenerateTTSUseCase, mock_tts_synthesizer: AsyncMock
    ) -> None:
        request = TTSRequest(
            session_id=uuid4(),
            timestamp=datetime.now(),
            text="Hello world",
            priority=TTSPriority.NORMAL,
            ducking=True,
            show_text=True,
        )
        result = await use_case.execute(request)
        assert result.success is True
        assert result.audio_path is not None
        mock_tts_synthesizer.synthesize.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_retry_on_tts_failure(
        self, use_case: GenerateTTSUseCase, mock_tts_synthesizer: AsyncMock
    ) -> None:
        mock_tts_synthesizer.synthesize.side_effect = [
            Exception("TTS failed first"),
            Exception("TTS failed second"),
            "/tmp/chappie_tts.mp3",
        ]
        request = TTSRequest(
            session_id=uuid4(),
            timestamp=datetime.now(),
            text="Hello",
            priority=TTSPriority.NORMAL,
            ducking=False,
            show_text=False,
        )
        result = await use_case.execute(request)
        assert result.success is True
        # 2 retries + original = 3 calls total, success on 3rd
        assert mock_tts_synthesizer.synthesize.call_count == 3

    @pytest.mark.asyncio
    async def test_should_fail_after_max_retries(
        self, use_case: GenerateTTSUseCase, mock_tts_synthesizer: AsyncMock
    ) -> None:
        mock_tts_synthesizer.synthesize.side_effect = Exception("TTS always fails")
        request = TTSRequest(
            session_id=uuid4(),
            timestamp=datetime.now(),
            text="Hello",
            priority=TTSPriority.NORMAL,
            ducking=False,
            show_text=False,
        )
        result = await use_case.execute(request)
        assert result.success is False
        assert result.error is not None
