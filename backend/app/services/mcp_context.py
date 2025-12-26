"""
MCPContextProvider for AI Context Enhancement (Story P11-3.1)

This module provides the MCPContextProvider class that gathers context
from user feedback history to enhance AI description prompts.

Architecture:
    - Queries EventFeedback by camera_id for feedback history
    - Calculates camera-specific accuracy rates
    - Extracts common correction patterns
    - Formats context for AI prompt injection
    - Fail-open design ensures AI works even if context fails

Flow:
    Event → MCPContextProvider.get_context(camera_id, event_time)
                                    ↓
                      Query recent feedback (last 50)
                                    ↓
                      Calculate accuracy rate
                                    ↓
                      Extract common corrections
                                    ↓
                      Build FeedbackContext
                                    ↓
                      Return AIContext
"""
import asyncio
import logging
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class FeedbackContext:
    """Context gathered from user feedback history."""
    accuracy_rate: Optional[float]  # 0.0-1.0, None if no feedback
    total_feedback: int
    common_corrections: List[str]  # Top 3 correction patterns
    recent_negative_reasons: List[str]  # Last 5 negative feedback reasons


@dataclass
class EntityContext:
    """Context about a matched entity (placeholder for P11-3.2)."""
    entity_id: str
    name: str
    entity_type: str  # person, vehicle
    attributes: Dict[str, str]
    last_seen: Optional[datetime]
    sighting_count: int


@dataclass
class CameraContext:
    """Context about camera location and patterns (placeholder for P11-3.3)."""
    camera_id: str
    location_hint: Optional[str]
    typical_objects: List[str]
    false_positive_patterns: List[str]


@dataclass
class TimePatternContext:
    """Context about time-of-day patterns (placeholder for P11-3.3)."""
    hour: int
    typical_activity_level: str  # low, medium, high
    is_unusual: bool
    typical_event_count: float


@dataclass
class AIContext:
    """Combined context for AI prompt generation."""
    feedback: Optional[FeedbackContext] = None
    entity: Optional[EntityContext] = None
    camera: Optional[CameraContext] = None
    time_pattern: Optional[TimePatternContext] = None


class MCPContextProvider:
    """
    Provides context for AI prompts based on accumulated feedback.

    This is the MVP implementation (P11-3.1) that focuses on feedback context.
    Entity, camera, and time pattern context will be added in subsequent stories.

    Attributes:
        FEEDBACK_LIMIT: Number of recent feedback items to query (50)
    """

    FEEDBACK_LIMIT = 50

    def __init__(self, db: Session = None):
        """
        Initialize MCPContextProvider.

        Args:
            db: Optional SQLAlchemy session. If None, must be provided to get_context().
        """
        self._db = db
        logger.info(
            "MCPContextProvider initialized",
            extra={"event_type": "mcp_context_provider_init"}
        )

    async def get_context(
        self,
        camera_id: str,
        event_time: datetime,
        entity_id: Optional[str] = None,
        db: Session = None,
    ) -> AIContext:
        """
        Gather context for AI prompt generation.

        Uses fail-open design: if any context component fails, returns
        partial context with None for failed components.

        Args:
            camera_id: UUID of the camera
            event_time: When the event occurred
            entity_id: Optional UUID of matched entity (for future P11-3.2)
            db: SQLAlchemy session (uses instance db if not provided)

        Returns:
            AIContext with available context components
        """
        start_time = time.time()
        session = db or self._db

        if not session:
            logger.warning(
                "No database session provided to get_context",
                extra={"event_type": "mcp_context_no_session", "camera_id": camera_id}
            )
            return AIContext()

        # Gather context components in parallel (fail-open)
        feedback_ctx = await self._safe_get_feedback_context(session, camera_id)

        # Entity, camera, and time pattern context are placeholders for future stories
        entity_ctx = None  # P11-3.2
        camera_ctx = None  # P11-3.3
        time_ctx = None    # P11-3.3

        context_gather_time_ms = (time.time() - start_time) * 1000

        # Log context gathering
        logger.info(
            f"MCP context gathered for camera {camera_id}",
            extra={
                "event_type": "mcp.context_gathered",
                "camera_id": camera_id,
                "duration_ms": round(context_gather_time_ms, 2),
                "has_feedback": feedback_ctx is not None,
                "has_entity": entity_ctx is not None,
                "has_camera": camera_ctx is not None,
                "has_time_pattern": time_ctx is not None,
            }
        )

        return AIContext(
            feedback=feedback_ctx,
            entity=entity_ctx,
            camera=camera_ctx,
            time_pattern=time_ctx,
        )

    async def _safe_get_feedback_context(
        self,
        db: Session,
        camera_id: str,
    ) -> Optional[FeedbackContext]:
        """
        Safely get feedback context with error handling.

        Implements fail-open: returns None on any error instead of propagating.

        Args:
            db: SQLAlchemy session
            camera_id: UUID of the camera

        Returns:
            FeedbackContext or None if error occurs
        """
        try:
            return await self._get_feedback_context(db, camera_id)
        except Exception as e:
            logger.warning(
                f"Failed to get feedback context for camera {camera_id}: {e}",
                extra={
                    "event_type": "mcp.context_error",
                    "component": "feedback",
                    "camera_id": camera_id,
                    "error": str(e),
                }
            )
            return None

    async def _get_feedback_context(
        self,
        db: Session,
        camera_id: str,
    ) -> Optional[FeedbackContext]:
        """
        Get feedback context for a camera.

        Queries recent feedback (last 50 items), calculates accuracy rate,
        and extracts common correction patterns.

        Args:
            db: SQLAlchemy session
            camera_id: UUID of the camera

        Returns:
            FeedbackContext with accuracy and correction patterns
        """
        from app.models.event_feedback import EventFeedback

        # Query recent feedback for this camera
        query = (
            db.query(EventFeedback)
            .filter(EventFeedback.camera_id == camera_id)
            .order_by(desc(EventFeedback.created_at))
            .limit(self.FEEDBACK_LIMIT)
        )

        feedbacks = query.all()
        total = len(feedbacks)

        if total == 0:
            return FeedbackContext(
                accuracy_rate=None,
                total_feedback=0,
                common_corrections=[],
                recent_negative_reasons=[],
            )

        # Calculate accuracy rate
        positive_count = sum(1 for f in feedbacks if f.rating == 'helpful')
        accuracy_rate = positive_count / total

        # Extract correction texts
        corrections = [f.correction for f in feedbacks if f.correction]

        # Get common correction patterns
        common_patterns = self._extract_common_patterns(corrections)

        # Get recent negative feedback reasons (last 5 with text)
        recent_negative = [
            f.correction for f in feedbacks[:5]
            if f.rating == 'not_helpful' and f.correction
        ]

        return FeedbackContext(
            accuracy_rate=accuracy_rate,
            total_feedback=total,
            common_corrections=common_patterns[:3],
            recent_negative_reasons=recent_negative[:5],
        )

    def _extract_common_patterns(self, corrections: List[str]) -> List[str]:
        """
        Extract common patterns from correction texts.

        Tokenizes corrections and finds most frequent meaningful words.

        Args:
            corrections: List of correction texts

        Returns:
            List of top 3 most common patterns
        """
        if not corrections:
            return []

        # Common words to exclude
        stop_words = {
            'the', 'a', 'an', 'is', 'was', 'it', 'this', 'that', 'not',
            'and', 'or', 'but', 'of', 'in', 'to', 'for', 'on', 'with',
            'be', 'are', 'were', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'i', 'you', 'he', 'she', 'we', 'they', 'my', 'your', 'its',
            'there', 'here', 'where', 'when', 'what', 'which', 'who',
            'actually', 'just', 'really', 'very', 'so', 'too', 'also',
        }

        # Count word frequencies
        word_counts: Counter = Counter()
        for correction in corrections:
            # Tokenize: lowercase, remove punctuation, split on whitespace
            words = re.findall(r'\b[a-z]+\b', correction.lower())
            # Filter stop words and short words
            meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
            word_counts.update(meaningful_words)

        # Get top patterns
        top_patterns = [word for word, _ in word_counts.most_common(5)]
        return top_patterns[:3]

    def format_for_prompt(self, context: AIContext) -> str:
        """
        Format context for inclusion in AI prompt.

        Generates human-readable context text that can be injected into
        AI prompts to improve description accuracy.

        Args:
            context: AIContext with gathered context components

        Returns:
            Formatted context string, empty string if no context
        """
        parts = []

        # Feedback context
        if context.feedback and context.feedback.accuracy_rate is not None:
            accuracy_pct = int(context.feedback.accuracy_rate * 100)
            parts.append(f"Previous accuracy for this camera: {accuracy_pct}%")

            if context.feedback.common_corrections:
                corrections_str = ", ".join(context.feedback.common_corrections)
                parts.append(f"Common corrections: {corrections_str}")

        # Entity context (placeholder for P11-3.2)
        if context.entity:
            parts.append(f"Known entity: {context.entity.name} ({context.entity.entity_type})")
            if context.entity.attributes:
                attrs = ", ".join(f"{k}={v}" for k, v in context.entity.attributes.items())
                parts.append(f"Entity attributes: {attrs}")

        # Camera context (placeholder for P11-3.3)
        if context.camera and context.camera.location_hint:
            parts.append(f"Camera location: {context.camera.location_hint}")

        # Time pattern context (placeholder for P11-3.3)
        if context.time_pattern and context.time_pattern.is_unusual:
            parts.append("Note: This is unusual activity for this time of day")

        return "\n".join(parts) if parts else ""


# Global singleton instance
_mcp_context_provider: Optional[MCPContextProvider] = None


def get_mcp_context_provider(db: Session = None) -> MCPContextProvider:
    """
    Get the global MCPContextProvider instance.

    Creates the instance on first call (lazy initialization).

    Args:
        db: Optional SQLAlchemy session to use

    Returns:
        MCPContextProvider singleton instance
    """
    global _mcp_context_provider

    if _mcp_context_provider is None:
        _mcp_context_provider = MCPContextProvider(db=db)
        logger.info(
            "Global MCPContextProvider instance created",
            extra={"event_type": "mcp_context_provider_singleton_created"}
        )

    return _mcp_context_provider


def reset_mcp_context_provider() -> None:
    """
    Reset the global MCPContextProvider instance.

    Useful for testing to ensure a fresh instance.
    """
    global _mcp_context_provider
    _mcp_context_provider = None
