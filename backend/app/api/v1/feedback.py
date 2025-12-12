"""
Feedback API endpoints - Story P4-5.2

Provides REST API for aggregate feedback statistics:
- GET /feedback/stats - Get aggregate feedback statistics with filtering
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from typing import Optional
from datetime import date, datetime, timezone, timedelta
import logging

from app.core.database import get_db
from app.models.event_feedback import EventFeedback
from app.models.camera import Camera
from app.schemas.feedback import (
    FeedbackStatsResponse,
    CameraFeedbackStats,
    DailyFeedbackStats,
    CorrectionSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    camera_id: Optional[str] = Query(
        None,
        description="Filter by camera UUID to get per-camera accuracy"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Filter feedback created on or after this date (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="Filter feedback created on or before this date (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db)
):
    """
    Get aggregate feedback statistics for AI description accuracy monitoring.

    Returns overall accuracy metrics, per-camera breakdown, daily trends,
    and common correction patterns.

    **Query Parameters:**
    - `camera_id`: Optional filter to get stats for a specific camera
    - `start_date`: Optional filter for feedback on or after this date
    - `end_date`: Optional filter for feedback on or before this date

    **Response Fields:**
    - `total_count`: Total number of feedback submissions
    - `helpful_count`: Number of helpful ratings
    - `not_helpful_count`: Number of not helpful ratings
    - `accuracy_rate`: Percentage of helpful ratings (helpful / total * 100)
    - `feedback_by_camera`: Per-camera breakdown with accuracy rates
    - `daily_trend`: Daily feedback counts for the last 30 days (or specified range)
    - `top_corrections`: Most common correction patterns (top 10)

    **Performance:**
    Optimized for <200ms response time with 10,000+ feedback records.

    **Examples:**
    ```
    GET /api/v1/feedback/stats
    GET /api/v1/feedback/stats?camera_id=abc123
    GET /api/v1/feedback/stats?start_date=2025-12-01&end_date=2025-12-31
    ```
    """
    try:
        # Build base filter conditions
        filters = []

        if camera_id:
            filters.append(EventFeedback.camera_id == camera_id)

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            filters.append(EventFeedback.created_at >= start_datetime)

        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
            filters.append(EventFeedback.created_at <= end_datetime)

        # 1. Calculate overall aggregate statistics
        aggregate_query = db.query(
            func.count(EventFeedback.id).label('total'),
            func.sum(case((EventFeedback.rating == 'helpful', 1), else_=0)).label('helpful'),
            func.sum(case((EventFeedback.rating == 'not_helpful', 1), else_=0)).label('not_helpful'),
        )

        if filters:
            aggregate_query = aggregate_query.filter(and_(*filters))

        stats = aggregate_query.first()

        total_count = stats.total or 0
        helpful_count = stats.helpful or 0
        not_helpful_count = stats.not_helpful or 0
        accuracy_rate = (helpful_count / total_count * 100) if total_count > 0 else 0.0

        # 2. Calculate per-camera breakdown
        feedback_by_camera = {}

        if not camera_id:  # Only calculate if not filtering by single camera
            camera_query = db.query(
                EventFeedback.camera_id,
                Camera.name.label('camera_name'),
                func.count(EventFeedback.id).label('total'),
                func.sum(case((EventFeedback.rating == 'helpful', 1), else_=0)).label('helpful'),
                func.sum(case((EventFeedback.rating == 'not_helpful', 1), else_=0)).label('not_helpful'),
            ).outerjoin(
                Camera, EventFeedback.camera_id == Camera.id
            ).filter(
                EventFeedback.camera_id.isnot(None)
            )

            if filters:
                camera_query = camera_query.filter(and_(*filters))

            camera_query = camera_query.group_by(
                EventFeedback.camera_id, Camera.name
            )

            camera_results = camera_query.all()

            for row in camera_results:
                cam_total = row.total or 0
                cam_helpful = row.helpful or 0
                cam_not_helpful = row.not_helpful or 0
                cam_accuracy = (cam_helpful / cam_total * 100) if cam_total > 0 else 0.0

                feedback_by_camera[row.camera_id] = CameraFeedbackStats(
                    camera_id=row.camera_id,
                    camera_name=row.camera_name or f"Camera {row.camera_id[:8]}",
                    helpful_count=cam_helpful,
                    not_helpful_count=cam_not_helpful,
                    accuracy_rate=round(cam_accuracy, 1)
                )
        else:
            # When filtering by camera_id, include that camera's stats
            camera = db.query(Camera).filter(Camera.id == camera_id).first()
            camera_name = camera.name if camera else f"Camera {camera_id[:8]}"

            feedback_by_camera[camera_id] = CameraFeedbackStats(
                camera_id=camera_id,
                camera_name=camera_name,
                helpful_count=helpful_count,
                not_helpful_count=not_helpful_count,
                accuracy_rate=round(accuracy_rate, 1)
            )

        # 3. Calculate daily trend (last 30 days or specified range)
        daily_trend = []

        # Determine date range for trend
        if start_date and end_date:
            trend_start = start_date
            trend_end = end_date
        elif start_date:
            trend_start = start_date
            trend_end = date.today()
        elif end_date:
            trend_start = end_date - timedelta(days=30)
            trend_end = end_date
        else:
            trend_end = date.today()
            trend_start = trend_end - timedelta(days=30)

        trend_start_dt = datetime.combine(trend_start, datetime.min.time()).replace(tzinfo=timezone.utc)
        trend_end_dt = datetime.combine(trend_end, datetime.max.time()).replace(tzinfo=timezone.utc)

        trend_filters = [
            EventFeedback.created_at >= trend_start_dt,
            EventFeedback.created_at <= trend_end_dt,
        ]

        if camera_id:
            trend_filters.append(EventFeedback.camera_id == camera_id)

        # Use func.date for SQLite compatibility
        daily_query = db.query(
            func.date(EventFeedback.created_at).label('date'),
            func.sum(case((EventFeedback.rating == 'helpful', 1), else_=0)).label('helpful_count'),
            func.sum(case((EventFeedback.rating == 'not_helpful', 1), else_=0)).label('not_helpful_count'),
        ).filter(
            and_(*trend_filters)
        ).group_by(
            func.date(EventFeedback.created_at)
        ).order_by(
            func.date(EventFeedback.created_at)
        )

        daily_results = daily_query.all()

        for row in daily_results:
            # Handle both string dates (SQLite) and date objects
            if isinstance(row.date, str):
                day = datetime.strptime(row.date, '%Y-%m-%d').date()
            else:
                day = row.date

            daily_trend.append(DailyFeedbackStats(
                date=day,
                helpful_count=row.helpful_count or 0,
                not_helpful_count=row.not_helpful_count or 0
            ))

        # 4. Get top corrections (most common correction patterns)
        top_corrections = []

        correction_query = db.query(
            EventFeedback.correction,
            func.count(EventFeedback.id).label('count')
        ).filter(
            EventFeedback.correction.isnot(None),
            EventFeedback.correction != ''
        )

        if filters:
            correction_query = correction_query.filter(and_(*filters))

        correction_query = correction_query.group_by(
            EventFeedback.correction
        ).order_by(
            func.count(EventFeedback.id).desc()
        ).limit(10)

        correction_results = correction_query.all()

        for row in correction_results:
            top_corrections.append(CorrectionSummary(
                correction_text=row.correction,
                count=row.count
            ))

        logger.info(
            f"Feedback stats retrieved: total={total_count}, helpful={helpful_count}, "
            f"accuracy={accuracy_rate:.1f}%, cameras={len(feedback_by_camera)}, "
            f"filters={{camera_id={camera_id}, start_date={start_date}, end_date={end_date}}}"
        )

        return FeedbackStatsResponse(
            total_count=total_count,
            helpful_count=helpful_count,
            not_helpful_count=not_helpful_count,
            accuracy_rate=round(accuracy_rate, 1),
            feedback_by_camera=feedback_by_camera,
            daily_trend=daily_trend,
            top_corrections=top_corrections
        )

    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}", exc_info=True)
        raise
