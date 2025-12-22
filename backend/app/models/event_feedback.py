"""EventFeedback SQLAlchemy ORM model for user feedback on AI event descriptions

Story P4-5.1: Feedback Collection UI
Story P4-5.2: Feedback Storage & API - Added camera_id for aggregate statistics
Story P9-3.3: Package False Positive Feedback - Added correction_type for specific corrections
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime, timezone


class EventFeedback(Base):
    """
    User feedback on AI-generated event descriptions.

    Allows users to rate descriptions as helpful/not helpful and provide
    optional correction text to improve AI accuracy over time.

    Attributes:
        id: UUID primary key
        event_id: Foreign key to events table (unique - one feedback per event)
        camera_id: Denormalized camera ID for efficient aggregate statistics (P4-5.2)
        rating: User rating - 'helpful' or 'not_helpful'
        correction: Optional correction text (max 500 chars enforced at API level)
        correction_type: Optional correction type for specific feedback (P9-3.3)
            - 'not_package': User marked package detection as incorrect
            - (Future: 'not_person', 'not_vehicle', 'not_animal')
        created_at: When feedback was submitted
        updated_at: When feedback was last modified
    """

    __tablename__ = "event_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(
        String,
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,  # One feedback per event
        index=True
    )
    # Story P4-5.2: Denormalized camera_id for efficient aggregate queries
    camera_id = Column(
        String,
        ForeignKey('cameras.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    rating = Column(String(20), nullable=False)  # 'helpful' or 'not_helpful'
    correction = Column(Text, nullable=True)  # Optional correction text
    # Story P9-3.3: Correction type for specific feedback (e.g., 'not_package')
    correction_type = Column(String(50), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship back to Event
    event = relationship("Event", back_populates="feedback")
    # Relationship to Camera (for aggregate statistics)
    camera = relationship("Camera", foreign_keys=[camera_id])

    __table_args__ = (
        UniqueConstraint('event_id', name='uq_event_feedback_event_id'),
    )

    def __repr__(self):
        return f"<EventFeedback(id={self.id}, event_id={self.event_id}, camera_id={self.camera_id}, rating={self.rating}, correction_type={self.correction_type})>"
