"""EventFrame SQLAlchemy ORM model for storing AI analysis frames"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime, timezone


class EventFrame(Base):
    """
    Database model for storing frames used in AI analysis.

    Represents individual frames extracted from video clips for multi-frame
    AI analysis. Each frame is stored as a JPEG file on disk with metadata
    tracked in this table.

    Story P8-2.1: Store All Analysis Frames During Event Processing

    Attributes:
        id: UUID primary key
        event_id: Foreign key to events table (CASCADE delete)
        frame_number: 1-indexed frame number within the event
        frame_path: Relative path to frame file (e.g., "frames/{event_id}/frame_001.jpg")
        timestamp_offset_ms: Milliseconds from video start when frame was captured
        width: Frame width in pixels
        height: Frame height in pixels
        file_size_bytes: Frame file size in bytes
        created_at: Record creation timestamp (UTC with timezone)
    """

    __tablename__ = "event_frames"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(
        String,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    frame_number = Column(Integer, nullable=False)  # 1-indexed
    frame_path = Column(String(500), nullable=False)  # Relative path to file
    timestamp_offset_ms = Column(Integer, nullable=False)  # ms from video start
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship back to Event
    event = relationship("Event", back_populates="frames")

    __table_args__ = (
        UniqueConstraint('event_id', 'frame_number', name='uq_event_frame_number'),
        Index('idx_event_frames_event_id', 'event_id'),
    )

    def __repr__(self):
        return f"<EventFrame(id={self.id}, event_id={self.event_id}, frame_number={self.frame_number})>"
