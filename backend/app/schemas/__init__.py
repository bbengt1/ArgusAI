"""Pydantic schemas for request/response validation"""
from app.schemas.camera import (
    CameraBase,
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraTestResponse,
)
from app.schemas.motion import (
    BoundingBox,
    MotionConfigUpdate,
    MotionConfigResponse,
    MotionTestRequest,
    MotionTestResponse,
    MotionEventResponse,
    MotionEventStatsResponse,
    DetectionZone,
    DetectionSchedule,
)
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
    # Story P4-5.2: Feedback statistics schemas
    CameraFeedbackStats,
    DailyFeedbackStats,
    CorrectionSummary,
    FeedbackStatsResponse,
)

__all__ = [
    "CameraBase",
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraTestResponse",
    "BoundingBox",
    "MotionConfigUpdate",
    "MotionConfigResponse",
    "MotionTestRequest",
    "MotionTestResponse",
    "MotionEventResponse",
    "MotionEventStatsResponse",
    "DetectionZone",
    "DetectionSchedule",
    "FeedbackCreate",
    "FeedbackUpdate",
    "FeedbackResponse",
    # Story P4-5.2: Feedback statistics schemas
    "CameraFeedbackStats",
    "DailyFeedbackStats",
    "CorrectionSummary",
    "FeedbackStatsResponse",
]
