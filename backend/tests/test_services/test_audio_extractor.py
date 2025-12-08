"""
Unit tests for AudioExtractor (Story P3-5.1)

Tests cover:
- AC1: Returns WAV bytes (16kHz, mono), extraction within 2s
- AC2: No audio track returns None with appropriate log
- AC3: Silent audio returns bytes, logs level metrics
- AC4: Singleton pattern with get/reset functions
- AC5: Audio level detection (RMS, peak amplitude)
- Error handling: FileNotFoundError, av.FFmpegError, generic errors
"""
import pytest
import io
import wave
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import numpy as np

from app.services.audio_extractor import (
    AudioExtractor,
    get_audio_extractor,
    reset_audio_extractor,
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_WIDTH,
    SILENCE_RMS_THRESHOLD,
    SILENCE_DB_THRESHOLD,
)


class TestAudioExtractorConstants:
    """Test service constants are properly defined"""

    def test_sample_rate(self):
        """AC1: Verify sample rate is 16kHz for Whisper compatibility"""
        assert AUDIO_SAMPLE_RATE == 16000

    def test_channels(self):
        """AC1: Verify mono channel output"""
        assert AUDIO_CHANNELS == 1

    def test_sample_width(self):
        """AC1: Verify 16-bit PCM (2 bytes per sample)"""
        assert AUDIO_SAMPLE_WIDTH == 2

    def test_silence_thresholds(self):
        """AC5: Verify silence detection thresholds are defined"""
        assert SILENCE_RMS_THRESHOLD == 0.001
        assert SILENCE_DB_THRESHOLD == -60


class TestAudioExtractorInit:
    """Test AudioExtractor initialization"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton before each test"""
        reset_audio_extractor()
        yield
        reset_audio_extractor()

    def test_init_sets_defaults(self):
        """AC4: Verify initialization with correct defaults"""
        extractor = AudioExtractor()

        assert extractor.sample_rate == AUDIO_SAMPLE_RATE
        assert extractor.channels == AUDIO_CHANNELS
        assert extractor.sample_width == AUDIO_SAMPLE_WIDTH


class TestAudioExtractorSingleton:
    """Test singleton pattern (AC4)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset singleton before each test"""
        reset_audio_extractor()
        yield
        reset_audio_extractor()

    def test_get_audio_extractor_returns_instance(self):
        """AC4: Verify get_audio_extractor returns AudioExtractor instance"""
        extractor = get_audio_extractor()

        assert isinstance(extractor, AudioExtractor)

    def test_get_audio_extractor_returns_same_instance(self):
        """AC4: Singleton returns same instance"""
        extractor1 = get_audio_extractor()
        extractor2 = get_audio_extractor()

        assert extractor1 is extractor2

    def test_reset_audio_extractor_clears_singleton(self):
        """AC4: Reset allows new instance creation"""
        extractor1 = get_audio_extractor()
        reset_audio_extractor()
        extractor2 = get_audio_extractor()

        assert extractor1 is not extractor2


class TestAudioLevelCalculation:
    """Test _calculate_audio_level method (AC5)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create extractor for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    def test_calculate_audio_level_empty_array(self):
        """AC5: Empty array returns zero levels"""
        samples = np.array([])
        rms, peak = self.extractor._calculate_audio_level(samples)

        assert rms == 0.0
        assert peak == 0.0

    def test_calculate_audio_level_silence(self):
        """AC5: Silent audio (zeros) returns zero levels"""
        samples = np.zeros(1000, dtype=np.float64)
        rms, peak = self.extractor._calculate_audio_level(samples)

        assert rms == 0.0
        assert peak == 0.0

    def test_calculate_audio_level_full_scale(self):
        """AC5: Full scale audio returns level of 1.0"""
        # All samples at +1.0
        samples = np.ones(1000, dtype=np.float64)
        rms, peak = self.extractor._calculate_audio_level(samples)

        assert rms == 1.0
        assert peak == 1.0

    def test_calculate_audio_level_half_scale(self):
        """AC5: Half scale audio returns correct RMS"""
        samples = np.ones(1000, dtype=np.float64) * 0.5
        rms, peak = self.extractor._calculate_audio_level(samples)

        assert rms == 0.5
        assert peak == 0.5

    def test_calculate_audio_level_sine_wave(self):
        """AC5: Sine wave RMS is approximately 0.707"""
        # Generate sine wave
        t = np.linspace(0, 2 * np.pi * 10, 1000)
        samples = np.sin(t)
        rms, peak = self.extractor._calculate_audio_level(samples)

        # RMS of sine wave is 1/sqrt(2) = 0.707
        assert abs(rms - 0.707) < 0.01
        assert abs(peak - 1.0) < 0.01


class TestRmsToDb:
    """Test _rms_to_db method (AC5)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create extractor for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    def test_rms_to_db_full_scale(self):
        """AC5: Full scale (1.0) is 0 dB"""
        db = self.extractor._rms_to_db(1.0)
        assert db == 0.0

    def test_rms_to_db_half_scale(self):
        """AC5: Half scale (0.5) is approximately -6 dB"""
        db = self.extractor._rms_to_db(0.5)
        # 20 * log10(0.5) = -6.02 dB
        assert abs(db - (-6.02)) < 0.1

    def test_rms_to_db_zero(self):
        """AC5: Zero RMS returns -96 dB (noise floor)"""
        db = self.extractor._rms_to_db(0.0)
        assert db == -96.0

    def test_rms_to_db_very_low(self):
        """AC5: Very low RMS is clamped to -96 dB"""
        db = self.extractor._rms_to_db(0.0000001)
        assert db == -96.0


class TestIsSilent:
    """Test _is_silent method (AC3, AC5)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create extractor for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    def test_is_silent_below_threshold(self):
        """AC3: RMS below threshold is silent"""
        assert self.extractor._is_silent(0.0005) is True
        assert self.extractor._is_silent(0.0) is True

    def test_is_silent_above_threshold(self):
        """AC3: RMS above threshold is not silent"""
        assert self.extractor._is_silent(0.01) is False
        assert self.extractor._is_silent(0.5) is False

    def test_is_silent_at_threshold(self):
        """AC3: RMS at exactly threshold is not silent"""
        assert self.extractor._is_silent(SILENCE_RMS_THRESHOLD) is False


class TestEncodeWav:
    """Test _encode_wav method (AC1)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create extractor for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    def test_encode_wav_returns_bytes(self):
        """AC1: Returns bytes"""
        samples = np.zeros(1000, dtype=np.int16)
        result = self.extractor._encode_wav(samples, 16000)

        assert isinstance(result, bytes)

    def test_encode_wav_magic_bytes(self):
        """AC1: WAV file starts with RIFF header"""
        samples = np.zeros(1000, dtype=np.int16)
        result = self.extractor._encode_wav(samples, 16000)

        # WAV files start with "RIFF"
        assert result[:4] == b'RIFF'
        # Contains "WAVE" marker
        assert result[8:12] == b'WAVE'

    def test_encode_wav_correct_format(self):
        """AC1: WAV has correct sample rate and channels"""
        samples = np.zeros(1000, dtype=np.int16)
        result = self.extractor._encode_wav(samples, 16000)

        # Parse WAV to verify format
        buffer = io.BytesIO(result)
        with wave.open(buffer, 'rb') as wav:
            assert wav.getnchannels() == 1  # Mono
            assert wav.getframerate() == 16000  # 16kHz
            assert wav.getsampwidth() == 2  # 16-bit


class TestExtractAudio:
    """Test extract_audio method (AC1, AC2, AC3)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    @pytest.mark.asyncio
    async def test_extract_audio_file_not_found(self):
        """AC2/Error: FileNotFoundError returns None"""
        result = await self.extractor.extract_audio(
            Path("/nonexistent/video.mp4")
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_audio_logs_file_not_found(self):
        """AC2/Error: Logs error with file path on FileNotFoundError"""
        with patch("app.services.audio_extractor.logger") as mock_logger:
            await self.extractor.extract_audio(
                Path("/nonexistent/video.mp4")
            )

            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_extract_audio_av_error_returns_none(self):
        """Error: av.FFmpegError returns None"""
        import av

        with patch("app.services.audio_extractor.av.open") as mock_open:
            mock_open.side_effect = av.FFmpegError(0, "Test error")

            result = await self.extractor.extract_audio(
                Path("/test/video.mp4")
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_extract_audio_av_error_logs(self):
        """Error: Logs error on av.FFmpegError"""
        import av

        with patch("app.services.audio_extractor.av.open") as mock_open:
            mock_open.side_effect = av.FFmpegError(0, "Test error")

            with patch("app.services.audio_extractor.logger") as mock_logger:
                await self.extractor.extract_audio(
                    Path("/test/video.mp4")
                )

                mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_extract_audio_generic_error_returns_none(self):
        """Error: Generic exceptions return None"""
        with patch("app.services.audio_extractor.av.open") as mock_open:
            mock_open.side_effect = RuntimeError("Unexpected error")

            result = await self.extractor.extract_audio(
                Path("/test/video.mp4")
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_extract_audio_no_audio_stream(self):
        """AC2: No audio stream returns None"""
        with patch("av.open") as mock_open:
            mock_container = MagicMock()
            mock_container.streams.audio = []
            mock_container.__enter__ = MagicMock(return_value=mock_container)
            mock_container.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_container

            result = await self.extractor.extract_audio(
                Path("/test/video.mp4")
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_extract_audio_no_audio_stream_logs(self):
        """AC2: Logs 'No audio track found in clip' message"""
        with patch("av.open") as mock_open:
            mock_container = MagicMock()
            mock_container.streams.audio = []
            mock_container.__enter__ = MagicMock(return_value=mock_container)
            mock_container.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_container

            with patch("app.services.audio_extractor.logger") as mock_logger:
                await self.extractor.extract_audio(
                    Path("/test/video.mp4")
                )

                # Check info was called with "no audio track" message
                info_calls = [str(c) for c in mock_logger.info.call_args_list]
                assert any("no audio" in c.lower() for c in info_calls)


class TestExtractAudioWithMockedContainer:
    """Test extract_audio with properly mocked PyAV container"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    def _create_mock_container(self, audio_samples: np.ndarray, sample_rate: int = 48000):
        """Create a mock PyAV container with audio stream"""
        mock_container = MagicMock()

        # Mock audio stream
        mock_audio_stream = MagicMock()
        mock_audio_stream.sample_rate = sample_rate
        mock_audio_stream.channels = 2
        mock_audio_stream.codec_context.name = "aac"
        mock_audio_stream.format.name = "fltp"
        mock_container.streams.audio = [mock_audio_stream]

        # Mock audio frame
        mock_frame = MagicMock()
        mock_frame.to_ndarray.return_value = audio_samples

        # Mock resampler
        mock_resampled_frame = MagicMock()
        # Return samples as int16 after resampling
        resampled_samples = (audio_samples * 32767).astype(np.int16)
        if resampled_samples.ndim > 1:
            resampled_samples = resampled_samples[0]  # Take first channel for mono
        mock_resampled_frame.to_ndarray.return_value = resampled_samples

        # Mock decode to return frame
        mock_container.decode.return_value = [mock_frame]

        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=False)

        return mock_container, mock_resampled_frame

    @pytest.mark.asyncio
    async def test_extract_audio_returns_wav_bytes(self):
        """AC1: Extract audio returns WAV bytes"""
        # Create some audio samples
        samples = np.random.randn(1, 1000).astype(np.float32) * 0.5

        mock_container, mock_resampled = self._create_mock_container(samples)

        with patch("av.open", return_value=mock_container):
            with patch("av.AudioResampler") as mock_resampler_class:
                mock_resampler = MagicMock()
                mock_resampler.resample.return_value = [mock_resampled]
                mock_resampler_class.return_value = mock_resampler

                result = await self.extractor.extract_audio(
                    Path("/test/video.mp4")
                )

                assert result is not None
                assert isinstance(result, bytes)
                # Check RIFF header
                assert result[:4] == b'RIFF'

    @pytest.mark.asyncio
    async def test_extract_audio_wav_format_correct(self):
        """AC1: WAV format is 16kHz mono"""
        samples = np.random.randn(1, 1000).astype(np.float32) * 0.5

        mock_container, mock_resampled = self._create_mock_container(samples)

        with patch("av.open", return_value=mock_container):
            with patch("av.AudioResampler") as mock_resampler_class:
                mock_resampler = MagicMock()
                mock_resampler.resample.return_value = [mock_resampled]
                mock_resampler_class.return_value = mock_resampler

                result = await self.extractor.extract_audio(
                    Path("/test/video.mp4")
                )

                # Parse WAV and verify format
                buffer = io.BytesIO(result)
                with wave.open(buffer, 'rb') as wav:
                    assert wav.getnchannels() == 1
                    assert wav.getframerate() == 16000
                    assert wav.getsampwidth() == 2

    @pytest.mark.asyncio
    async def test_extract_audio_logs_level_metrics(self):
        """AC3, AC5: Logs audio level metrics"""
        samples = np.random.randn(1, 1000).astype(np.float32) * 0.5

        mock_container, mock_resampled = self._create_mock_container(samples)

        with patch("av.open", return_value=mock_container):
            with patch("av.AudioResampler") as mock_resampler_class:
                mock_resampler = MagicMock()
                mock_resampler.resample.return_value = [mock_resampled]
                mock_resampler_class.return_value = mock_resampler

                with patch("app.services.audio_extractor.logger") as mock_logger:
                    await self.extractor.extract_audio(
                        Path("/test/video.mp4")
                    )

                    # Check that audio level analysis was logged
                    info_calls = [str(c) for c in mock_logger.info.call_args_list]
                    assert any("audio_level_analysis" in c for c in info_calls)


class TestExtractAudioSilentAudio:
    """Test silent audio handling (AC3)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    @pytest.mark.asyncio
    async def test_silent_audio_returns_bytes(self):
        """AC3: Silent audio track returns bytes (not None)"""
        # Create silent audio (all zeros)
        silent_samples = np.zeros((1, 1000), dtype=np.float32)

        mock_container = MagicMock()
        mock_audio_stream = MagicMock()
        mock_audio_stream.sample_rate = 48000
        mock_audio_stream.channels = 1
        mock_audio_stream.codec_context.name = "aac"
        mock_audio_stream.format.name = "s16"
        mock_container.streams.audio = [mock_audio_stream]

        mock_frame = MagicMock()
        mock_frame.to_ndarray.return_value = silent_samples

        mock_resampled_frame = MagicMock()
        mock_resampled_frame.to_ndarray.return_value = np.zeros(1000, dtype=np.int16)

        mock_container.decode.return_value = [mock_frame]
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=False)

        with patch("av.open", return_value=mock_container):
            with patch("av.AudioResampler") as mock_resampler_class:
                mock_resampler = MagicMock()
                mock_resampler.resample.return_value = [mock_resampled_frame]
                mock_resampler_class.return_value = mock_resampler

                result = await self.extractor.extract_audio(
                    Path("/test/video.mp4")
                )

                # Silent audio should still return bytes
                assert result is not None
                assert isinstance(result, bytes)
                assert result[:4] == b'RIFF'

    @pytest.mark.asyncio
    async def test_silent_audio_logs_is_silent_true(self):
        """AC3: Silent audio logs is_silent=True in metrics"""
        silent_samples = np.zeros((1, 1000), dtype=np.float32)

        mock_container = MagicMock()
        mock_audio_stream = MagicMock()
        mock_audio_stream.sample_rate = 48000
        mock_audio_stream.channels = 1
        mock_audio_stream.codec_context.name = "aac"
        mock_audio_stream.format.name = "s16"
        mock_container.streams.audio = [mock_audio_stream]

        mock_frame = MagicMock()
        mock_frame.to_ndarray.return_value = silent_samples

        mock_resampled_frame = MagicMock()
        mock_resampled_frame.to_ndarray.return_value = np.zeros(1000, dtype=np.int16)

        mock_container.decode.return_value = [mock_frame]
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=False)

        with patch("av.open", return_value=mock_container):
            with patch("av.AudioResampler") as mock_resampler_class:
                mock_resampler = MagicMock()
                mock_resampler.resample.return_value = [mock_resampled_frame]
                mock_resampler_class.return_value = mock_resampler

                with patch("app.services.audio_extractor.logger") as mock_logger:
                    await self.extractor.extract_audio(
                        Path("/test/video.mp4")
                    )

                    # Check that is_silent was logged
                    info_calls = [str(c) for c in mock_logger.info.call_args_list]
                    assert any("is_silent" in c for c in info_calls)


class TestExtractAudioLogging:
    """Test logging behavior"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for tests"""
        reset_audio_extractor()
        self.extractor = AudioExtractor()
        yield
        reset_audio_extractor()

    @pytest.mark.asyncio
    async def test_logs_extraction_start(self):
        """Logs start of extraction with clip path"""
        with patch("app.services.audio_extractor.logger") as mock_logger:
            with patch("av.open") as mock_open:
                mock_open.side_effect = FileNotFoundError("Not found")

                await self.extractor.extract_audio(
                    Path("/test/video.mp4")
                )

                # Check that info was called for start
                mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_logs_success_with_metrics(self):
        """Logs successful extraction with wav size and duration"""
        samples = np.random.randn(1, 1000).astype(np.float32) * 0.5

        mock_container = MagicMock()
        mock_audio_stream = MagicMock()
        mock_audio_stream.sample_rate = 48000
        mock_audio_stream.channels = 1
        mock_audio_stream.codec_context.name = "aac"
        mock_audio_stream.format.name = "s16"
        mock_container.streams.audio = [mock_audio_stream]

        mock_frame = MagicMock()
        mock_frame.to_ndarray.return_value = samples

        mock_resampled = MagicMock()
        mock_resampled.to_ndarray.return_value = (samples[0] * 32767).astype(np.int16)

        mock_container.decode.return_value = [mock_frame]
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=False)

        with patch("av.open", return_value=mock_container):
            with patch("av.AudioResampler") as mock_resampler_class:
                mock_resampler = MagicMock()
                mock_resampler.resample.return_value = [mock_resampled]
                mock_resampler_class.return_value = mock_resampler

                with patch("app.services.audio_extractor.logger") as mock_logger:
                    await self.extractor.extract_audio(
                        Path("/test/video.mp4")
                    )

                    # Should have logged success
                    info_calls = [str(c) for c in mock_logger.info.call_args_list]
                    assert any("success" in c.lower() or "complete" in c.lower() for c in info_calls)
