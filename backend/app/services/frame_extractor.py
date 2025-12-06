"""
FrameExtractor for extracting frames from video clips (Story P3-2.1)

Provides functionality to:
- Extract multiple frames from video clips for AI analysis
- Select frames using evenly-spaced strategy (first/last guaranteed)
- Encode frames as JPEG with configurable quality
- Resize frames to max width for optimal AI token cost

Architecture Reference: docs/architecture.md#Phase-3-Service-Architecture
"""
import io
import logging
from pathlib import Path
from typing import List, Optional

import av
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Frame extraction configuration (Story P3-2.1, FR8)
FRAME_EXTRACT_DEFAULT_COUNT = 5
FRAME_EXTRACT_MIN_COUNT = 3
FRAME_EXTRACT_MAX_COUNT = 10
FRAME_JPEG_QUALITY = 85
FRAME_MAX_WIDTH = 1280


class FrameExtractor:
    """
    Service for extracting frames from video clips.

    Extracts evenly-spaced frames from video files for multi-frame AI analysis.
    Returns JPEG-encoded bytes suitable for sending to vision AI providers.

    Key features:
    - Evenly-spaced frame selection (first and last frames always included)
    - JPEG encoding at configurable quality (default 85%)
    - Automatic resize to max width (default 1280px)
    - Graceful error handling (returns empty list on failure)

    Follows singleton pattern matching ClipService for consistency.

    Attributes:
        default_frame_count: Default number of frames to extract (5)
        jpeg_quality: JPEG encoding quality 0-100 (85)
        max_width: Maximum frame width in pixels (1280)
    """

    def __init__(self):
        """
        Initialize FrameExtractor with default configuration.
        """
        self.default_frame_count = FRAME_EXTRACT_DEFAULT_COUNT
        self.jpeg_quality = FRAME_JPEG_QUALITY
        self.max_width = FRAME_MAX_WIDTH

        logger.info(
            "FrameExtractor initialized",
            extra={
                "event_type": "frame_extractor_init",
                "default_frame_count": self.default_frame_count,
                "jpeg_quality": self.jpeg_quality,
                "max_width": self.max_width
            }
        )

    def _calculate_frame_indices(self, total_frames: int, frame_count: int) -> List[int]:
        """
        Calculate evenly spaced frame indices.

        Always includes first frame (index 0) and last frame (total_frames - 1).
        Intermediate frames are evenly distributed.

        Args:
            total_frames: Total number of frames in the video
            frame_count: Number of frames to extract

        Returns:
            List of frame indices to extract

        Example:
            total_frames=300, frame_count=5 -> [0, 74, 149, 224, 299]
        """
        if total_frames <= 0:
            return []

        if frame_count <= 0:
            return []

        # If requesting more frames than available, return all
        if frame_count >= total_frames:
            return list(range(total_frames))

        # If only 1 frame requested, return first frame
        if frame_count == 1:
            return [0]

        # Calculate evenly spaced indices
        # Formula ensures first frame is 0 and last frame is total_frames - 1
        indices = []
        for i in range(frame_count):
            # Spread frames evenly across the video
            index = int((i * (total_frames - 1)) / (frame_count - 1))
            indices.append(index)

        return indices

    def _encode_frame(self, frame: np.ndarray) -> bytes:
        """
        Encode a frame as JPEG bytes.

        Resizes frame to max_width if larger, maintaining aspect ratio.
        Uses PIL for high-quality JPEG encoding.

        Args:
            frame: RGB numpy array (H, W, 3)

        Returns:
            JPEG-encoded bytes
        """
        # Convert numpy array to PIL Image
        img = Image.fromarray(frame)

        # Resize if needed (maintain aspect ratio)
        if img.width > self.max_width:
            ratio = self.max_width / img.width
            new_size = (self.max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Encode as JPEG
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=self.jpeg_quality)
        return buffer.getvalue()

    async def extract_frames(
        self,
        clip_path: Path,
        frame_count: int = 5,
        strategy: str = "evenly_spaced"
    ) -> List[bytes]:
        """
        Extract frames from a video clip.

        Extracts evenly-spaced frames from the video for AI analysis.
        First and last frames are always included.

        Args:
            clip_path: Path to the video file (MP4)
            frame_count: Number of frames to extract (3-10, default 5)
            strategy: Selection strategy (currently only "evenly_spaced")

        Returns:
            List of JPEG-encoded frame bytes.
            Returns empty list on any error (never raises).

        Note:
            - Extraction completes within 2 seconds for 10-second clips (NFR2)
            - JPEG quality is 85% (configurable)
            - Frames are resized to max 1280px width
        """
        logger.info(
            "Starting frame extraction",
            extra={
                "event_type": "frame_extraction_start",
                "clip_path": str(clip_path),
                "frame_count": frame_count,
                "strategy": strategy
            }
        )

        # Validate frame_count within bounds
        if frame_count < FRAME_EXTRACT_MIN_COUNT:
            frame_count = FRAME_EXTRACT_MIN_COUNT
            logger.debug(
                f"Frame count adjusted to minimum: {FRAME_EXTRACT_MIN_COUNT}",
                extra={
                    "event_type": "frame_count_adjusted",
                    "original": frame_count,
                    "adjusted": FRAME_EXTRACT_MIN_COUNT
                }
            )
        elif frame_count > FRAME_EXTRACT_MAX_COUNT:
            frame_count = FRAME_EXTRACT_MAX_COUNT
            logger.debug(
                f"Frame count adjusted to maximum: {FRAME_EXTRACT_MAX_COUNT}",
                extra={
                    "event_type": "frame_count_adjusted",
                    "original": frame_count,
                    "adjusted": FRAME_EXTRACT_MAX_COUNT
                }
            )

        try:
            # Open video file with PyAV
            with av.open(str(clip_path)) as container:
                # Get video stream
                if not container.streams.video:
                    logger.warning(
                        "No video stream found in file",
                        extra={
                            "event_type": "frame_extraction_no_video",
                            "clip_path": str(clip_path)
                        }
                    )
                    return []

                stream = container.streams.video[0]

                # Get total frame count
                # Try stream.frames first, fall back to duration estimate
                total_frames = stream.frames
                if total_frames is None or total_frames <= 0:
                    # Estimate from duration and frame rate
                    if container.duration and stream.average_rate:
                        duration_seconds = container.duration / 1_000_000.0
                        total_frames = int(duration_seconds * float(stream.average_rate))
                    else:
                        logger.warning(
                            "Cannot determine total frames",
                            extra={
                                "event_type": "frame_extraction_unknown_frames",
                                "clip_path": str(clip_path)
                            }
                        )
                        return []

                if total_frames <= 0:
                    logger.warning(
                        "Video has no frames",
                        extra={
                            "event_type": "frame_extraction_no_frames",
                            "clip_path": str(clip_path)
                        }
                    )
                    return []

                # Calculate which frames to extract
                indices = self._calculate_frame_indices(total_frames, frame_count)

                if not indices:
                    logger.warning(
                        "No frame indices calculated",
                        extra={
                            "event_type": "frame_extraction_no_indices",
                            "clip_path": str(clip_path),
                            "total_frames": total_frames,
                            "frame_count": frame_count
                        }
                    )
                    return []

                logger.debug(
                    f"Extracting {len(indices)} frames from {total_frames} total",
                    extra={
                        "event_type": "frame_extraction_indices",
                        "clip_path": str(clip_path),
                        "total_frames": total_frames,
                        "indices": indices
                    }
                )

                # Extract frames at calculated indices
                frames: List[bytes] = []
                current_frame_index = 0

                # Decode all frames and pick the ones we need
                # This is more reliable than seeking for many codecs
                for frame in container.decode(video=0):
                    if current_frame_index in indices:
                        # Convert to RGB numpy array
                        img_array = frame.to_ndarray(format='rgb24')
                        # Encode as JPEG
                        jpeg_bytes = self._encode_frame(img_array)
                        frames.append(jpeg_bytes)

                        # Remove this index from the set we're looking for
                        indices.remove(current_frame_index)

                        # If we've got all frames, stop early
                        if not indices:
                            break

                    current_frame_index += 1

                logger.info(
                    f"Frame extraction complete: {len(frames)} frames",
                    extra={
                        "event_type": "frame_extraction_success",
                        "clip_path": str(clip_path),
                        "frames_extracted": len(frames),
                        "total_bytes": sum(len(f) for f in frames)
                    }
                )

                return frames

        except FileNotFoundError as e:
            logger.error(
                f"Video file not found: {clip_path}",
                extra={
                    "event_type": "frame_extraction_file_not_found",
                    "clip_path": str(clip_path),
                    "error": str(e)
                }
            )
            return []

        except av.FFmpegError as e:
            logger.error(
                f"PyAV error processing video: {e}",
                extra={
                    "event_type": "frame_extraction_av_error",
                    "clip_path": str(clip_path),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return []

        except Exception as e:
            logger.error(
                f"Unexpected error extracting frames: {type(e).__name__}",
                extra={
                    "event_type": "frame_extraction_error",
                    "clip_path": str(clip_path),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return []


# Singleton instance
_frame_extractor: Optional[FrameExtractor] = None


def get_frame_extractor() -> FrameExtractor:
    """
    Get the singleton FrameExtractor instance.

    Creates the instance on first call.

    Returns:
        FrameExtractor singleton instance
    """
    global _frame_extractor
    if _frame_extractor is None:
        _frame_extractor = FrameExtractor()
    return _frame_extractor


def reset_frame_extractor() -> None:
    """
    Reset the singleton instance (useful for testing).
    """
    global _frame_extractor
    _frame_extractor = None
