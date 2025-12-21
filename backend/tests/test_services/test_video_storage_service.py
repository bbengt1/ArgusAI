"""
Unit tests for VideoStorageService (Story P8-3.2)

Tests video download and storage functionality for Protect cameras.
"""
import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.video_storage_service import (
    VideoStorageService,
    VIDEO_DIR,
    DOWNLOAD_TIMEOUT,
    get_video_storage_service,
    reset_video_storage_service,
)


class TestVideoStorageService:
    """Tests for VideoStorageService functionality."""

    @pytest.fixture
    def mock_protect_service(self):
        """Create a mock ProtectService."""
        mock_service = MagicMock()
        mock_service._connections = {}
        return mock_service

    @pytest.fixture
    def video_service(self, mock_protect_service):
        """Create a VideoStorageService instance with mocked dependencies."""
        return VideoStorageService(mock_protect_service)

    @pytest.fixture
    def temp_video_dir(self, tmp_path):
        """Create a temporary video directory."""
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        return video_dir

    def test_init_creates_video_dir(self, mock_protect_service, tmp_path):
        """Test that VideoStorageService creates video directory on init."""
        with patch("app.services.video_storage_service.VIDEO_DIR", str(tmp_path / "videos")):
            service = VideoStorageService(mock_protect_service)
            # Directory should be created
            assert (tmp_path / "videos").exists()

    def test_get_video_path(self, video_service):
        """Test _get_video_path returns correct path format."""
        event_id = "test-event-123"
        path = video_service._get_video_path(event_id)

        assert path.name == f"{event_id}.mp4"
        assert str(path).endswith(".mp4")

    def test_get_video_path_if_exists_not_found(self, video_service):
        """Test get_video_path_if_exists returns None when video doesn't exist."""
        path = video_service.get_video_path_if_exists("nonexistent-event")
        assert path is None

    def test_get_video_path_if_exists_found(self, video_service, temp_video_dir):
        """Test get_video_path_if_exists returns path when video exists."""
        event_id = "existing-event"
        with patch("app.services.video_storage_service.VIDEO_DIR", str(temp_video_dir)):
            # Create a test video file
            video_file = temp_video_dir / f"{event_id}.mp4"
            video_file.write_bytes(b"fake video content")

            # Reinitialize service with patched path
            service = VideoStorageService(video_service._protect_service)
            path = service.get_video_path_if_exists(event_id)

            assert path is not None
            assert path.exists()

    def test_get_storage_stats_empty_dir(self, video_service, temp_video_dir):
        """Test get_storage_stats with empty video directory."""
        with patch("app.services.video_storage_service.VIDEO_DIR", str(temp_video_dir)):
            service = VideoStorageService(video_service._protect_service)
            stats = service.get_storage_stats()

            assert stats["total_videos"] == 0
            assert stats["total_size_mb"] == 0.0
            assert stats["oldest_video_age_days"] == 0

    def test_get_storage_stats_with_videos(self, video_service, temp_video_dir):
        """Test get_storage_stats with existing videos."""
        with patch("app.services.video_storage_service.VIDEO_DIR", str(temp_video_dir)):
            # Create test video files
            for i in range(3):
                video_file = temp_video_dir / f"event-{i}.mp4"
                video_file.write_bytes(b"x" * (1024 * 1024))  # 1MB each

            service = VideoStorageService(video_service._protect_service)
            stats = service.get_storage_stats()

            assert stats["total_videos"] == 3
            assert pytest.approx(stats["total_size_mb"], rel=0.1) == 3.0

    def test_delete_video_not_found(self, video_service, temp_video_dir):
        """Test delete_video returns False when video doesn't exist."""
        with patch("app.services.video_storage_service.VIDEO_DIR", str(temp_video_dir)):
            service = VideoStorageService(video_service._protect_service)
            result = service.delete_video("nonexistent-event")

            assert result is False

    def test_delete_video_success(self, video_service, temp_video_dir):
        """Test delete_video successfully removes video."""
        event_id = "deletable-event"
        with patch("app.services.video_storage_service.VIDEO_DIR", str(temp_video_dir)):
            # Create test video file
            video_file = temp_video_dir / f"{event_id}.mp4"
            video_file.write_bytes(b"video content")

            service = VideoStorageService(video_service._protect_service)
            result = service.delete_video(event_id)

            assert result is True
            assert not video_file.exists()

    @pytest.mark.asyncio
    async def test_download_video_controller_not_connected(self, video_service):
        """Test download_video returns None when controller not connected."""
        result = await video_service.download_video(
            event_id="test-event",
            controller_id="unknown-controller",
            camera_id="camera-1",
            event_start=datetime.now(timezone.utc),
            event_end=datetime.now(timezone.utc) + timedelta(seconds=10)
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_download_video_success(self, video_service, temp_video_dir):
        """Test successful video download."""
        event_id = "download-test"
        controller_id = "test-controller"
        camera_id = "test-camera"

        # Setup mock client
        mock_client = AsyncMock()

        async def mock_get_camera_video(**kwargs):
            # Simulate writing video to output file
            output_file = kwargs["output_file"]
            output_file.write_bytes(b"downloaded video content")

        mock_client.get_camera_video = mock_get_camera_video
        video_service._protect_service._connections[controller_id] = mock_client

        with patch("app.services.video_storage_service.VIDEO_DIR", str(temp_video_dir)):
            service = VideoStorageService(video_service._protect_service)
            service._protect_service._connections[controller_id] = mock_client

            result = await service.download_video(
                event_id=event_id,
                controller_id=controller_id,
                camera_id=camera_id,
                event_start=datetime.now(timezone.utc),
                event_end=datetime.now(timezone.utc) + timedelta(seconds=10)
            )

            assert result is not None
            assert result.exists()
            assert result.name == f"{event_id}.mp4"


class TestVideoStorageServiceSingleton:
    """Tests for VideoStorageService singleton pattern."""

    def test_reset_video_storage_service(self):
        """Test reset clears the singleton instance."""
        # Ensure clean state
        reset_video_storage_service()

        # Create mock protect service
        mock_protect = MagicMock()
        mock_protect._connections = {}

        # Patch where get_protect_service is called from (inside the function)
        with patch("app.services.protect_service.get_protect_service", return_value=mock_protect):
            # Get instance
            service1 = get_video_storage_service()
            assert service1 is not None

            # Reset
            reset_video_storage_service()

            # Get new instance
            service2 = get_video_storage_service()

            # Should be different instances (new one created after reset)
            assert service1 is not service2
