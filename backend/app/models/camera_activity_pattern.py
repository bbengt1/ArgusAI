"""CameraActivityPattern SQLAlchemy ORM model (Story P4-3.5)

Stores time-based activity patterns for cameras for the Temporal Context Engine.
Patterns are pre-calculated periodically (default: hourly) and persisted for
fast lookup (<50ms) during event processing.

Pattern data includes:
- Hourly distribution: Events per hour (0-23) across all days
- Daily distribution: Events per day-of-week (0-6, Monday=0)
- Peak hours: Hours with above-average activity
- Quiet hours: Hours with minimal activity
- Average events per day: Mean daily event count

Patterns enable AI descriptions to include timing context like:
- "This is typical activity for this time"
- "Unusual - this camera is normally quiet at this hour"
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, Index
import uuid

from app.core.database import Base


class CameraActivityPattern(Base):
    """
    Pre-calculated activity patterns for a camera.

    Stores time-based activity patterns that are calculated periodically
    and used for fast timing analysis during event processing.

    Attributes:
        id: UUID primary key
        camera_id: Foreign key to cameras (one pattern per camera)
        hourly_distribution: JSON dict of events per hour {"0": count, ..., "23": count}
        daily_distribution: JSON dict of events per day-of-week {"0": count, ..., "6": count}
        peak_hours: JSON array of peak activity hours ["09", "14", "17"]
        quiet_hours: JSON array of quiet hours ["02", "03", "04"]
        average_events_per_day: Mean daily event count
        calculation_window_days: Number of days used for calculation (default: 30)
        last_calculated_at: When patterns were last recalculated
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """

    __tablename__ = "camera_activity_patterns"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="UUID primary key"
    )
    camera_id = Column(
        String,
        ForeignKey("cameras.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        doc="Foreign key to cameras (one pattern per camera)"
    )
    hourly_distribution = Column(
        Text,
        nullable=False,
        doc="JSON dict: events per hour {'0': count, ..., '23': count}"
    )
    daily_distribution = Column(
        Text,
        nullable=False,
        doc="JSON dict: events per day-of-week {'0': count, ..., '6': count}"
    )
    peak_hours = Column(
        Text,
        nullable=False,
        doc="JSON array: peak activity hours ['09', '14', '17']"
    )
    quiet_hours = Column(
        Text,
        nullable=False,
        doc="JSON array: quiet hours ['02', '03', '04']"
    )
    average_events_per_day = Column(
        Float,
        nullable=False,
        doc="Mean daily event count"
    )
    calculation_window_days = Column(
        Integer,
        nullable=False,
        default=30,
        doc="Number of days used for calculation"
    )
    last_calculated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="When patterns were last recalculated"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Record creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Record last update timestamp"
    )

    __table_args__ = (
        Index("idx_camera_activity_patterns_camera_id", "camera_id"),
        Index("idx_camera_activity_patterns_last_calculated", "last_calculated_at"),
    )

    def __repr__(self):
        return (
            f"<CameraActivityPattern(id={self.id}, camera_id={self.camera_id}, "
            f"avg_events={self.average_events_per_day:.1f}, "
            f"last_calc={self.last_calculated_at})>"
        )
