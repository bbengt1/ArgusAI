"""
Tests for motion events CSV export API endpoint

Story: P6-4.1 - Implement Motion Events CSV Export
"""
import pytest
import csv
import io
import json
from datetime import datetime, timezone, timedelta

from app.models.motion_event import MotionEvent
from app.models.camera import Camera


class TestMotionEventsExport:
    """Test suite for GET /api/v1/motion-events/export endpoint"""

    def _create_camera(self, db_session, camera_id="test-camera-1", name="Front Door"):
        """Helper to create a camera for testing"""
        camera = Camera(
            id=camera_id,
            name=name,
            type="rtsp",
            rtsp_url="rtsp://192.168.1.100:554/stream",
            source_type="rtsp",
            is_enabled=True
        )
        db_session.add(camera)
        db_session.commit()
        return camera

    def _create_motion_event(
        self,
        db_session,
        camera_id="test-camera-1",
        timestamp=None,
        confidence=0.85,
        algorithm="mog2",
        bounding_box=None
    ):
        """Helper to create a motion event for testing"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        event = MotionEvent(
            camera_id=camera_id,
            timestamp=timestamp,
            confidence=confidence,
            algorithm_used=algorithm,
            bounding_box=json.dumps(bounding_box) if bounding_box else None
        )
        db_session.add(event)
        db_session.commit()
        return event

    def _parse_csv_response(self, response_content):
        """Parse CSV content from response"""
        reader = csv.DictReader(io.StringIO(response_content))
        return list(reader)

    # AC #1: GET /api/v1/motion-events/export?format=csv endpoint created
    def test_export_endpoint_returns_200_with_csv_format(self, api_client, db_session):
        """Test endpoint returns 200 with valid format=csv parameter"""
        self._create_camera(db_session)
        self._create_motion_event(db_session)

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_export_endpoint_returns_422_with_invalid_format(self, api_client):
        """Test endpoint returns 422 with invalid format parameter"""
        response = api_client.get("/api/v1/motion-events/export?format=json")

        assert response.status_code == 422

    def test_export_endpoint_returns_422_without_format_param(self, api_client):
        """Test endpoint returns 422 when format parameter is missing"""
        response = api_client.get("/api/v1/motion-events/export")

        assert response.status_code == 422

    # AC #2: CSV columns include required fields
    def test_csv_contains_all_required_columns(self, api_client, db_session):
        """Test CSV contains all required columns in correct order"""
        self._create_camera(db_session)
        self._create_motion_event(db_session)

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        rows = self._parse_csv_response(response.text)
        assert len(rows) == 1

        expected_columns = [
            "timestamp", "camera_id", "camera_name", "confidence",
            "algorithm", "x", "y", "width", "height", "zone_id"
        ]
        assert list(rows[0].keys()) == expected_columns

    def test_csv_camera_name_from_camera_table(self, api_client, db_session):
        """Test camera_name is populated from Camera table join"""
        camera = self._create_camera(db_session, camera_id="cam-1", name="Backyard Camera")
        self._create_motion_event(db_session, camera_id="cam-1")

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        rows = self._parse_csv_response(response.text)
        assert rows[0]["camera_name"] == "Backyard Camera"

    def test_csv_camera_name_fallback_to_id_if_camera_deleted(self, api_client, db_session):
        """Test camera_name uses camera_id as fallback if camera not found"""
        # Create motion event without corresponding camera
        event = MotionEvent(
            camera_id="deleted-camera-id",
            timestamp=datetime.now(timezone.utc),
            confidence=0.75,
            algorithm_used="mog2"
        )
        db_session.add(event)
        db_session.commit()

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        rows = self._parse_csv_response(response.text)
        assert rows[0]["camera_name"] == "deleted-camera-id"

    def test_csv_bounding_box_parsed_correctly(self, api_client, db_session):
        """Test bounding_box JSON is parsed correctly into x,y,width,height columns"""
        self._create_camera(db_session)
        bbox = {"x": 100, "y": 200, "width": 50, "height": 75}
        self._create_motion_event(db_session, bounding_box=bbox)

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        rows = self._parse_csv_response(response.text)
        assert rows[0]["x"] == "100"
        assert rows[0]["y"] == "200"
        assert rows[0]["width"] == "50"
        assert rows[0]["height"] == "75"

    def test_csv_handles_null_bounding_box(self, api_client, db_session):
        """Test null bounding_box results in empty strings"""
        self._create_camera(db_session)
        self._create_motion_event(db_session, bounding_box=None)

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        rows = self._parse_csv_response(response.text)
        assert rows[0]["x"] == ""
        assert rows[0]["y"] == ""
        assert rows[0]["width"] == ""
        assert rows[0]["height"] == ""

    def test_csv_confidence_and_algorithm_values(self, api_client, db_session):
        """Test confidence and algorithm values are correctly exported"""
        self._create_camera(db_session)
        self._create_motion_event(db_session, confidence=0.92, algorithm="knn")

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        rows = self._parse_csv_response(response.text)
        assert rows[0]["confidence"] == "0.92"
        assert rows[0]["algorithm"] == "knn"

    # AC #3: Date range filtering
    def test_start_date_filter_excludes_earlier_events(self, api_client, db_session):
        """Test start_date filter excludes events before date"""
        self._create_camera(db_session)

        # Event before filter date (should be excluded)
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc)
        )
        # Event on filter date (should be included)
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc)
        )

        response = api_client.get("/api/v1/motion-events/export?format=csv&start_date=2025-12-10")

        rows = self._parse_csv_response(response.text)
        assert len(rows) == 1
        assert "2025-12-10" in rows[0]["timestamp"]

    def test_end_date_filter_excludes_later_events(self, api_client, db_session):
        """Test end_date filter excludes events after date"""
        self._create_camera(db_session)

        # Event before filter date (should be included)
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 5, 10, 0, 0, tzinfo=timezone.utc)
        )
        # Event after filter date (should be excluded)
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        )

        response = api_client.get("/api/v1/motion-events/export?format=csv&end_date=2025-12-10")

        rows = self._parse_csv_response(response.text)
        assert len(rows) == 1
        assert "2025-12-05" in rows[0]["timestamp"]

    def test_date_range_combined_filter(self, api_client, db_session):
        """Test combined start_date and end_date filters"""
        self._create_camera(db_session)

        # Events outside range
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc)
        )
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
        )
        # Events inside range
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc)
        )
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        )

        response = api_client.get(
            "/api/v1/motion-events/export?format=csv&start_date=2025-12-05&end_date=2025-12-16"
        )

        rows = self._parse_csv_response(response.text)
        assert len(rows) == 2

    # AC #4: Camera filtering
    def test_camera_id_filter_returns_only_matching_events(self, api_client, db_session):
        """Test camera_id filter returns only events from that camera"""
        self._create_camera(db_session, camera_id="camera-1", name="Camera 1")
        self._create_camera(db_session, camera_id="camera-2", name="Camera 2")

        self._create_motion_event(db_session, camera_id="camera-1")
        self._create_motion_event(db_session, camera_id="camera-2")

        response = api_client.get("/api/v1/motion-events/export?format=csv&camera_id=camera-1")

        rows = self._parse_csv_response(response.text)
        assert len(rows) == 1
        assert rows[0]["camera_id"] == "camera-1"

    def test_combined_camera_and_date_filters(self, api_client, db_session):
        """Test combined camera_id and date range filters"""
        self._create_camera(db_session, camera_id="camera-1", name="Camera 1")
        self._create_camera(db_session, camera_id="camera-2", name="Camera 2")

        # Camera 1, in date range
        self._create_motion_event(
            db_session,
            camera_id="camera-1",
            timestamp=datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc)
        )
        # Camera 1, out of date range
        self._create_motion_event(
            db_session,
            camera_id="camera-1",
            timestamp=datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc)
        )
        # Camera 2, in date range
        self._create_motion_event(
            db_session,
            camera_id="camera-2",
            timestamp=datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc)
        )

        response = api_client.get(
            "/api/v1/motion-events/export?format=csv&camera_id=camera-1&start_date=2025-12-05"
        )

        rows = self._parse_csv_response(response.text)
        assert len(rows) == 1
        assert rows[0]["camera_id"] == "camera-1"

    # AC #5: Streaming response
    def test_streaming_response_headers(self, api_client, db_session):
        """Test streaming response has correct Content-Type header"""
        self._create_camera(db_session)
        self._create_motion_event(db_session)

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        assert "text/csv" in response.headers["content-type"]

    # AC #6: Filename includes date range
    def test_filename_includes_date_range_when_filtered(self, api_client, db_session):
        """Test filename includes date range when filters applied"""
        self._create_camera(db_session)
        self._create_motion_event(db_session)

        response = api_client.get(
            "/api/v1/motion-events/export?format=csv&start_date=2025-12-01&end_date=2025-12-17"
        )

        content_disposition = response.headers.get("content-disposition", "")
        assert "motion_events_2025-12-01_2025-12-17.csv" in content_disposition

    def test_filename_uses_all_when_no_date_filters(self, api_client, db_session):
        """Test filename uses 'all' when no date filters"""
        self._create_camera(db_session)
        self._create_motion_event(db_session)

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        content_disposition = response.headers.get("content-disposition", "")
        assert "motion_events_all.csv" in content_disposition

    def test_filename_with_start_date_only(self, api_client, db_session):
        """Test filename format when only start_date provided"""
        self._create_camera(db_session)
        self._create_motion_event(db_session)

        response = api_client.get("/api/v1/motion-events/export?format=csv&start_date=2025-12-01")

        content_disposition = response.headers.get("content-disposition", "")
        assert "motion_events_2025-12-01_latest.csv" in content_disposition

    def test_filename_with_end_date_only(self, api_client, db_session):
        """Test filename format when only end_date provided"""
        self._create_camera(db_session)
        self._create_motion_event(db_session)

        response = api_client.get("/api/v1/motion-events/export?format=csv&end_date=2025-12-17")

        content_disposition = response.headers.get("content-disposition", "")
        assert "motion_events_earliest_2025-12-17.csv" in content_disposition

    # Edge cases
    def test_empty_result_set(self, api_client, db_session):
        """Test export with empty result set returns headers only"""
        response = api_client.get("/api/v1/motion-events/export?format=csv")

        assert response.status_code == 200
        rows = self._parse_csv_response(response.text)
        assert len(rows) == 0
        # Verify headers are still present
        assert "timestamp" in response.text
        assert "camera_id" in response.text

    def test_export_with_multiple_events_in_order(self, api_client, db_session):
        """Test multiple events are exported in timestamp order"""
        self._create_camera(db_session)

        # Create events out of order
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        )
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc)
        )
        self._create_motion_event(
            db_session,
            timestamp=datetime(2025, 12, 12, 10, 0, 0, tzinfo=timezone.utc)
        )

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        rows = self._parse_csv_response(response.text)
        assert len(rows) == 3
        # Should be ordered by timestamp ascending
        assert "2025-12-10" in rows[0]["timestamp"]
        assert "2025-12-12" in rows[1]["timestamp"]
        assert "2025-12-15" in rows[2]["timestamp"]

    def test_export_handles_invalid_bounding_box_json(self, api_client, db_session):
        """Test export handles malformed bounding_box JSON gracefully"""
        self._create_camera(db_session)

        event = MotionEvent(
            camera_id="test-camera-1",
            timestamp=datetime.now(timezone.utc),
            confidence=0.85,
            algorithm_used="mog2",
            bounding_box="not valid json"  # Invalid JSON
        )
        db_session.add(event)
        db_session.commit()

        response = api_client.get("/api/v1/motion-events/export?format=csv")

        assert response.status_code == 200
        rows = self._parse_csv_response(response.text)
        assert rows[0]["x"] == ""
        assert rows[0]["y"] == ""
