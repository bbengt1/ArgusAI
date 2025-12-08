"""
AudioExtractor for extracting audio tracks from video clips (Story P3-5.1)

Provides functionality to:
- Extract audio tracks from video clips for speech transcription
- Output audio as WAV bytes (16kHz, mono) for OpenAI Whisper compatibility
- Handle videos without audio tracks gracefully
- Detect audio levels and log metrics for diagnostics

Architecture Reference: docs/architecture.md#Phase-3-Service-Architecture
"""
import io
import logging
import math
import struct
import wave
from pathlib import Path
from typing import Optional, Tuple

import av
import numpy as np

logger = logging.getLogger(__name__)

# Audio extraction configuration (Story P3-5.1)
AUDIO_SAMPLE_RATE = 16000  # 16kHz for Whisper compatibility
AUDIO_CHANNELS = 1  # Mono
AUDIO_SAMPLE_WIDTH = 2  # 16-bit signed PCM (2 bytes per sample)

# Silence detection thresholds
SILENCE_RMS_THRESHOLD = 0.001  # RMS threshold for silence detection (linear scale)
SILENCE_DB_THRESHOLD = -60  # dB threshold for logging (corresponds to ~0.001 RMS)


class AudioExtractor:
    """
    Service for extracting audio tracks from video clips.

    Extracts audio from video files and converts it to WAV format
    suitable for speech transcription with OpenAI Whisper.

    Key features:
    - Extracts audio and resamples to 16kHz mono WAV
    - Handles videos without audio tracks (returns None)
    - Detects silence and logs audio level metrics
    - Graceful error handling (returns None, never raises)
    - Follows singleton pattern matching FrameExtractor

    Attributes:
        sample_rate: Target sample rate in Hz (16000)
        channels: Number of audio channels (1 for mono)
        sample_width: Sample width in bytes (2 for 16-bit PCM)
    """

    def __init__(self):
        """
        Initialize AudioExtractor with default configuration.
        """
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        self.sample_width = AUDIO_SAMPLE_WIDTH

        logger.info(
            "AudioExtractor initialized",
            extra={
                "event_type": "audio_extractor_init",
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "sample_width": self.sample_width
            }
        )

    def _calculate_audio_level(self, samples: np.ndarray) -> Tuple[float, float]:
        """
        Calculate RMS level and peak amplitude from audio samples.

        Args:
            samples: Audio samples as numpy array (normalized to -1.0 to 1.0)

        Returns:
            Tuple of (rms_level, peak_amplitude) as linear values (0.0 to 1.0)
        """
        if len(samples) == 0:
            return 0.0, 0.0

        # Ensure float array for calculations
        samples = samples.astype(np.float64)

        # Calculate RMS (Root Mean Square)
        rms = np.sqrt(np.mean(samples ** 2))

        # Calculate peak amplitude
        peak = np.max(np.abs(samples))

        return float(rms), float(peak)

    def _rms_to_db(self, rms: float) -> float:
        """
        Convert RMS level to decibels.

        Args:
            rms: RMS level as linear value (0.0 to 1.0)

        Returns:
            Level in dB (0 dB = full scale, negative = quieter)
        """
        if rms <= 0:
            return -96.0  # Below noise floor
        db = 20 * math.log10(rms)
        return max(-96.0, db)  # Clamp to reasonable range

    def _is_silent(self, rms: float) -> bool:
        """
        Determine if audio is silent based on RMS level.

        Args:
            rms: RMS level as linear value

        Returns:
            True if audio is considered silent
        """
        return rms < SILENCE_RMS_THRESHOLD

    def _encode_wav(self, samples: np.ndarray, sample_rate: int) -> bytes:
        """
        Encode audio samples as WAV bytes.

        Args:
            samples: Audio samples as numpy array (int16 values)
            sample_rate: Sample rate in Hz

        Returns:
            WAV file bytes
        """
        buffer = io.BytesIO()

        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())

        return buffer.getvalue()

    async def extract_audio(self, clip_path: Path) -> Optional[bytes]:
        """
        Extract audio from a video clip as WAV bytes.

        Extracts the audio track from the video file, resamples to 16kHz mono,
        and returns as WAV bytes suitable for OpenAI Whisper transcription.

        Args:
            clip_path: Path to the video file (MP4)

        Returns:
            WAV-encoded audio bytes on success, None if:
            - No audio track in video
            - File not found
            - Any error during extraction

        Note:
            - Extraction completes within 2 seconds for 10-second clips (NFR)
            - WAV format: 16kHz, mono, 16-bit PCM
            - Silent audio is still returned (downstream handles silence)
            - All errors are logged with structured format
        """
        logger.info(
            "Starting audio extraction",
            extra={
                "event_type": "audio_extraction_start",
                "clip_path": str(clip_path)
            }
        )

        try:
            # Open video file with PyAV
            with av.open(str(clip_path)) as container:
                # Check for audio stream
                if not container.streams.audio:
                    logger.info(
                        "No audio track found in clip",
                        extra={
                            "event_type": "audio_extraction_no_audio",
                            "clip_path": str(clip_path)
                        }
                    )
                    return None

                audio_stream = container.streams.audio[0]

                # Log source audio format
                logger.debug(
                    "Source audio stream detected",
                    extra={
                        "event_type": "audio_stream_info",
                        "clip_path": str(clip_path),
                        "codec": audio_stream.codec_context.name if audio_stream.codec_context else "unknown",
                        "sample_rate": audio_stream.sample_rate,
                        "channels": audio_stream.channels,
                        "format": str(audio_stream.format.name) if audio_stream.format else "unknown"
                    }
                )

                # Create resampler to convert to target format
                # Target: 16kHz, mono, signed 16-bit PCM
                resampler = av.AudioResampler(
                    format='s16',  # Signed 16-bit
                    layout='mono',  # Mono channel
                    rate=self.sample_rate  # 16kHz
                )

                # Decode and resample all audio frames
                audio_samples = []
                total_samples = 0

                for frame in container.decode(audio=0):
                    # Resample frame to target format
                    resampled_frames = resampler.resample(frame)

                    for resampled_frame in resampled_frames:
                        if resampled_frame is not None:
                            # Get audio data as numpy array
                            # s16 format: signed 16-bit integers
                            samples = resampled_frame.to_ndarray()

                            # Flatten if multi-dimensional (should be 1D after mono resample)
                            if samples.ndim > 1:
                                samples = samples.flatten()

                            audio_samples.append(samples)
                            total_samples += len(samples)

                # Check if we got any audio
                if not audio_samples:
                    logger.warning(
                        "No audio frames decoded from clip",
                        extra={
                            "event_type": "audio_extraction_no_frames",
                            "clip_path": str(clip_path)
                        }
                    )
                    return None

                # Concatenate all samples
                all_samples = np.concatenate(audio_samples)

                # Calculate audio levels for diagnostics
                # Convert int16 to float for level calculation
                samples_float = all_samples.astype(np.float64) / 32768.0
                rms_level, peak_level = self._calculate_audio_level(samples_float)
                rms_db = self._rms_to_db(rms_level)
                peak_db = self._rms_to_db(peak_level)
                is_silent = self._is_silent(rms_level)

                # Log audio level metrics (AC3, AC5)
                logger.info(
                    "Audio level analysis complete",
                    extra={
                        "event_type": "audio_level_analysis",
                        "clip_path": str(clip_path),
                        "rms_level": rms_level,
                        "rms_db": rms_db,
                        "peak_level": peak_level,
                        "peak_db": peak_db,
                        "is_silent": is_silent,
                        "total_samples": len(all_samples),
                        "duration_seconds": len(all_samples) / self.sample_rate
                    }
                )

                # Encode as WAV
                wav_bytes = self._encode_wav(all_samples.astype(np.int16), self.sample_rate)

                logger.info(
                    "Audio extraction complete",
                    extra={
                        "event_type": "audio_extraction_success",
                        "clip_path": str(clip_path),
                        "wav_size_bytes": len(wav_bytes),
                        "duration_seconds": len(all_samples) / self.sample_rate,
                        "is_silent": is_silent
                    }
                )

                return wav_bytes

        except FileNotFoundError as e:
            logger.error(
                f"Audio file not found: {clip_path}",
                extra={
                    "event_type": "audio_extraction_file_not_found",
                    "clip_path": str(clip_path),
                    "error": str(e)
                }
            )
            return None

        except av.FFmpegError as e:
            logger.error(
                f"PyAV error processing audio: {e}",
                extra={
                    "event_type": "audio_extraction_av_error",
                    "clip_path": str(clip_path),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return None

        except Exception as e:
            logger.error(
                f"Unexpected error extracting audio: {type(e).__name__}",
                extra={
                    "event_type": "audio_extraction_error",
                    "clip_path": str(clip_path),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return None


# Singleton instance
_audio_extractor: Optional[AudioExtractor] = None


def get_audio_extractor() -> AudioExtractor:
    """
    Get the singleton AudioExtractor instance.

    Creates the instance on first call.

    Returns:
        AudioExtractor singleton instance
    """
    global _audio_extractor
    if _audio_extractor is None:
        _audio_extractor = AudioExtractor()
    return _audio_extractor


def reset_audio_extractor() -> None:
    """
    Reset the singleton instance (useful for testing).
    """
    global _audio_extractor
    _audio_extractor = None
