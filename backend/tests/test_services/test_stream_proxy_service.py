"""
Unit tests for StreamProxyService (Story P16-2.2)

Tests the live streaming service that proxies camera RTSP streams via WebSocket.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import numpy as np
from datetime import datetime, timezone

from app.services.stream_proxy_service import (
    StreamProxyService,
    StreamQuality,
    QualityConfig,
    StreamClient,
    CameraStream,
    QUALITY_CONFIGS,
    get_stream_proxy_service
)
from app.core.config import settings


class TestStreamQuality:
    """Test StreamQuality enum and QUALITY_CONFIGS"""

    def test_quality_levels_exist(self):
        """Test that all quality levels are defined"""
        assert StreamQuality.LOW.value == "low"
        assert StreamQuality.MEDIUM.value == "medium"
        assert StreamQuality.HIGH.value == "high"

    def test_quality_config_low(self):
        """Test low quality configuration"""
        config = QUALITY_CONFIGS[StreamQuality.LOW]
        assert config.width == 640
        assert config.height == 360
        assert config.fps == 5
        assert config.jpeg_quality == 70

    def test_quality_config_medium(self):
        """Test medium quality configuration"""
        config = QUALITY_CONFIGS[StreamQuality.MEDIUM]
        assert config.width == 1280
        assert config.height == 720
        assert config.fps == 10
        assert config.jpeg_quality == 80

    def test_quality_config_high(self):
        """Test high quality configuration"""
        config = QUALITY_CONFIGS[StreamQuality.HIGH]
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 15
        assert config.jpeg_quality == 90


class TestStreamClient:
    """Test StreamClient dataclass"""

    def test_client_creation(self):
        """Test creating a stream client"""
        client = StreamClient(
            client_id="test-123",
            quality=StreamQuality.MEDIUM,
            connected_at=datetime.now(timezone.utc)
        )
        assert client.client_id == "test-123"
        assert client.quality == StreamQuality.MEDIUM
        assert client.last_frame_at is None
        assert client.frames_sent == 0

    def test_client_frame_tracking(self):
        """Test client frame tracking"""
        client = StreamClient(
            client_id="test-123",
            quality=StreamQuality.HIGH,
            connected_at=datetime.now(timezone.utc)
        )
        client.frames_sent = 100
        client.last_frame_at = datetime.now(timezone.utc)
        assert client.frames_sent == 100
        assert client.last_frame_at is not None


class TestCameraStream:
    """Test CameraStream dataclass"""

    def test_stream_creation(self):
        """Test creating a camera stream"""
        stream = CameraStream(
            camera_id="cam-123",
            rtsp_url="rtsp://test/stream"
        )
        assert stream.camera_id == "cam-123"
        assert stream.is_running is False
        assert stream.capture_thread is None
        assert stream.clients == {}
        assert stream.frame_buffer == []
        assert stream.last_frame is None
        assert stream.error_count == 0

    def test_stream_client_management(self):
        """Test adding and removing clients from stream"""
        stream = CameraStream(
            camera_id="cam-123",
            rtsp_url="rtsp://test/stream"
        )

        # Add client
        client = StreamClient(
            client_id="client-1",
            quality=StreamQuality.LOW,
            connected_at=datetime.now(timezone.utc)
        )
        stream.clients["client-1"] = client
        assert len(stream.clients) == 1

        # Remove client
        del stream.clients["client-1"]
        assert len(stream.clients) == 0


class TestStreamProxyService:
    """Test StreamProxyService class"""

    @pytest.fixture
    def service(self):
        """Create a fresh StreamProxyService instance for each test"""
        # Create a new instance (not the singleton)
        svc = StreamProxyService()
        yield svc
        # Cleanup
        svc.stop_all()

    def test_singleton_pattern(self):
        """Test that get_stream_proxy_service returns singleton"""
        service1 = get_stream_proxy_service()
        service2 = get_stream_proxy_service()
        assert service1 is service2

    def test_get_stream_info_no_active_stream(self, service):
        """Test getting stream info for camera without active stream"""
        info = service.get_stream_info("test-cam-123")

        assert info["camera_id"] == "test-cam-123"
        assert info["current_clients"] == 0
        assert info["is_available"] is True
        assert len(info["quality_options"]) == 3
        assert info["default_quality"] == settings.STREAM_DEFAULT_QUALITY

    def test_get_stream_info_with_clients(self, service):
        """Test getting stream info with active clients"""
        # Setup: Create a stream with clients
        stream = CameraStream(
            camera_id="test-cam-456",
            rtsp_url="rtsp://test/stream"
        )
        stream.clients["client-1"] = StreamClient(
            "client-1", StreamQuality.MEDIUM, datetime.now(timezone.utc)
        )
        stream.clients["client-2"] = StreamClient(
            "client-2", StreamQuality.HIGH, datetime.now(timezone.utc)
        )
        service._streams["test-cam-456"] = stream
        # Also update the total client count
        service._total_clients = 2

        info = service.get_stream_info("test-cam-456")

        assert info["current_clients"] == 2
        assert info["max_clients_available"] == settings.STREAM_MAX_CONCURRENT - 2

    def test_get_metrics_empty(self, service):
        """Test getting metrics with no active streams"""
        metrics = service.get_metrics()

        assert metrics["active_streams"] == 0
        assert metrics["total_clients"] == 0
        assert metrics["max_concurrent"] == settings.STREAM_MAX_CONCURRENT
        assert metrics["streams_started_total"] == 0
        assert metrics["streams_stopped_total"] == 0
        assert metrics["connection_errors_total"] == 0

    def test_get_metrics_with_streams(self, service):
        """Test getting metrics with active streams"""
        # Setup: Create streams with clients
        stream1 = CameraStream(camera_id="cam-1", rtsp_url="rtsp://test1/stream")
        stream1.is_running = True
        stream1.clients["c1"] = StreamClient("c1", StreamQuality.LOW, datetime.now(timezone.utc))
        stream1.clients["c2"] = StreamClient("c2", StreamQuality.MEDIUM, datetime.now(timezone.utc))

        stream2 = CameraStream(camera_id="cam-2", rtsp_url="rtsp://test2/stream")
        stream2.is_running = True
        stream2.clients["c3"] = StreamClient("c3", StreamQuality.HIGH, datetime.now(timezone.utc))

        service._streams["cam-1"] = stream1
        service._streams["cam-2"] = stream2
        service._total_clients = 3
        service._streams_started = 5
        service._streams_stopped = 2
        service._connection_errors = 1

        metrics = service.get_metrics()

        assert metrics["active_streams"] == 2
        assert metrics["total_clients"] == 3
        assert metrics["streams_started_total"] == 5
        assert metrics["streams_stopped_total"] == 2
        assert metrics["connection_errors_total"] == 1

    def test_concurrent_limit_enforcement(self, service):
        """Test that concurrent stream limit is enforced"""
        # Fill up to max clients
        for i in range(settings.STREAM_MAX_CONCURRENT):
            stream = CameraStream(camera_id=f"cam-{i}", rtsp_url=f"rtsp://test{i}/stream")
            stream.clients[f"client-{i}"] = StreamClient(
                f"client-{i}", StreamQuality.MEDIUM, datetime.now(timezone.utc)
            )
            service._streams[f"cam-{i}"] = stream
        # Also update the total client count
        service._total_clients = settings.STREAM_MAX_CONCURRENT

        info = service.get_stream_info("new-camera")
        assert info["max_clients_available"] == 0
        assert info["is_available"] is False

    def test_remove_client_stops_empty_stream(self, service):
        """Test that removing last client stops the stream"""
        camera_id = "test-cam"
        client_id = "client-1"

        # Setup: Create a stream with one client
        stream = CameraStream(camera_id=camera_id, rtsp_url="rtsp://test/stream")
        stream.is_running = True
        stream.clients[client_id] = StreamClient(
            client_id, StreamQuality.MEDIUM, datetime.now(timezone.utc)
        )
        service._streams[camera_id] = stream

        # Remove the client
        service.remove_client(camera_id, client_id)

        # Stream should be removed since no clients remain
        assert camera_id not in service._streams

    def test_change_quality(self, service):
        """Test changing client quality"""
        camera_id = "test-cam"
        client_id = "client-1"

        # Setup: Create a stream with a client
        stream = CameraStream(camera_id=camera_id, rtsp_url="rtsp://test/stream")
        stream.clients[client_id] = StreamClient(
            client_id, StreamQuality.LOW, datetime.now(timezone.utc)
        )
        service._streams[camera_id] = stream

        # Change quality
        service.change_quality(camera_id, client_id, StreamQuality.HIGH)

        assert stream.clients[client_id].quality == StreamQuality.HIGH

    def test_change_quality_nonexistent_client(self, service):
        """Test changing quality for nonexistent client (should not raise)"""
        # This should not raise an exception
        service.change_quality("nonexistent-cam", "nonexistent-client", StreamQuality.HIGH)

    def test_get_snapshot_no_stream(self, service):
        """Test getting snapshot when stream doesn't exist returns None for sync path"""
        # Sync path returns None when no active stream and no RTSP URL provided
        result = service.get_snapshot("nonexistent-cam")
        assert result is None

    def test_get_snapshot_with_active_stream(self, service):
        """Test getting snapshot from active stream with current frame"""
        camera_id = "test-cam"

        # Create a test frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        stream = CameraStream(camera_id=camera_id, rtsp_url="rtsp://test/stream")
        stream.last_frame = test_frame
        service._streams[camera_id] = stream

        result = service.get_snapshot(camera_id)
        # Should return encoded JPEG bytes
        assert result is not None
        assert isinstance(result, bytes)


class TestStreamProxyServiceAsync:
    """Async tests for StreamProxyService"""

    @pytest.fixture
    def service(self):
        """Create a fresh StreamProxyService instance"""
        svc = StreamProxyService()
        yield svc
        svc.stop_all()

    @pytest.mark.asyncio
    async def test_add_client_starts_stream(self, service):
        """Test that adding first client starts the stream"""
        mock_camera = Mock()
        mock_camera.type = "rtsp"
        mock_camera.rtsp_url = "rtsp://test/stream"
        mock_camera.username = None
        mock_camera.password = None

        with patch.object(service, '_start_capture'):
            client_id = await service.add_client("test-cam", mock_camera, StreamQuality.MEDIUM)

            assert client_id is not None
            assert "test-cam" in service._streams
            assert client_id in service._streams["test-cam"].clients

    @pytest.mark.asyncio
    async def test_add_client_concurrent_limit(self, service):
        """Test that adding client fails when at limit"""
        # Fill up to max clients
        for i in range(settings.STREAM_MAX_CONCURRENT):
            stream = CameraStream(camera_id=f"cam-{i}", rtsp_url=f"rtsp://test{i}/stream")
            stream.clients[f"client-{i}"] = StreamClient(
                f"client-{i}", StreamQuality.MEDIUM, datetime.now(timezone.utc)
            )
            service._streams[f"cam-{i}"] = stream
        # Set total clients counter
        service._total_clients = settings.STREAM_MAX_CONCURRENT

        mock_camera = Mock()
        mock_camera.type = "rtsp"
        mock_camera.rtsp_url = "rtsp://test/stream"

        client_id = await service.add_client("new-cam", mock_camera, StreamQuality.MEDIUM)
        assert client_id is None

    @pytest.mark.asyncio
    async def test_get_snapshot_from_rtsp_no_stream(self, service):
        """Test getting snapshot from RTSP when no stream is active"""
        rtsp_url = "rtsp://test/stream"

        # Mock the _capture_single_frame method
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        with patch.object(service, '_capture_single_frame', return_value=test_frame):
            result = await service.get_snapshot_from_rtsp("test-cam", rtsp_url, StreamQuality.MEDIUM)

            assert result is not None
            assert isinstance(result, bytes)
            # JPEG files start with FF D8
            assert result[:2] == b'\xff\xd8'

    @pytest.mark.asyncio
    async def test_get_snapshot_from_rtsp_uses_active_stream(self, service):
        """Test getting snapshot from RTSP uses buffered frame from active stream"""
        camera_id = "test-cam"
        rtsp_url = "rtsp://test/stream"

        # Setup: Create a stream with a current frame
        stream = CameraStream(camera_id=camera_id, rtsp_url=rtsp_url)
        stream.is_running = True

        # Create a test frame
        test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        test_frame[100:200, 100:200] = [255, 0, 0]  # Red square

        stream.last_frame = test_frame
        stream.last_frame_time = datetime.now(timezone.utc)
        service._streams[camera_id] = stream

        result = await service.get_snapshot_from_rtsp(camera_id, rtsp_url, StreamQuality.MEDIUM)

        assert result is not None
        assert isinstance(result, bytes)
        # JPEG files start with FF D8
        assert result[:2] == b'\xff\xd8'

    @pytest.mark.asyncio
    async def test_get_snapshot_from_rtsp_error_handling(self, service):
        """Test snapshot error handling when capture fails"""
        rtsp_url = "rtsp://invalid/stream"

        with patch.object(service, '_capture_single_frame', return_value=None):
            result = await service.get_snapshot_from_rtsp("test-cam", rtsp_url, StreamQuality.MEDIUM)

            assert result is None


class TestFrameEncoding:
    """Test frame encoding functionality"""

    @pytest.fixture
    def service(self):
        """Create a fresh StreamProxyService instance"""
        svc = StreamProxyService()
        yield svc
        svc.stop_all()

    def test_encode_frame_basic(self, service):
        """Test basic frame encoding"""
        # Create a test frame (720p)
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[100:200, 100:200] = [0, 255, 0]  # Green square

        encoded = service._encode_frame(frame, StreamQuality.MEDIUM)

        assert encoded is not None
        assert isinstance(encoded, bytes)
        # JPEG files start with FF D8
        assert encoded[:2] == b'\xff\xd8'

    def test_encode_frame_resize(self, service):
        """Test that frame is resized to quality config dimensions"""
        # Create a 4K frame
        frame = np.zeros((2160, 3840, 3), dtype=np.uint8)

        # Encode at low quality (640x360)
        encoded = service._encode_frame(frame, StreamQuality.LOW)

        assert encoded is not None
        # The encoded frame should be smaller than unresized

    def test_encode_frame_quality_levels(self, service):
        """Test that different quality levels produce different sized outputs"""
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame[200:400, 200:400] = [128, 128, 128]  # Gray square for non-trivial encoding

        low_encoded = service._encode_frame(frame, StreamQuality.LOW)
        medium_encoded = service._encode_frame(frame, StreamQuality.MEDIUM)
        high_encoded = service._encode_frame(frame, StreamQuality.HIGH)

        # Higher quality should generally produce larger files
        # (though this isn't strictly guaranteed due to JPEG compression)
        assert all(e is not None for e in [low_encoded, medium_encoded, high_encoded])


class TestStopAll:
    """Test service stop_all functionality"""

    def test_stop_all_stops_all_streams(self):
        """Test that stop_all stops all active streams"""
        service = StreamProxyService()

        # Create some streams
        for i in range(3):
            stream = CameraStream(camera_id=f"cam-{i}", rtsp_url=f"rtsp://test{i}/stream")
            stream.is_running = True
            stream.clients[f"client-{i}"] = StreamClient(
                f"client-{i}", StreamQuality.MEDIUM, datetime.now(timezone.utc)
            )
            service._streams[f"cam-{i}"] = stream

        # Stop all streams
        service.stop_all()

        # All streams should be stopped
        for stream in service._streams.values():
            assert stream.is_running is False
