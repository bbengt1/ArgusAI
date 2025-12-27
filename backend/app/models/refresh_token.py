"""
RefreshToken Model (Story P12-3.1)

Refresh tokens for mobile JWT authentication.
Tokens are stored as SHA-256 hashes for security.
Old tokens are revoked on rotation.
"""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class RefreshToken(Base):
    """
    Refresh tokens for mobile JWT authentication.

    Security features:
    - Tokens stored as SHA-256 hashes (never plaintext)
    - Old tokens revoked on rotation (single-use)
    - Grace period for concurrent refresh requests
    - All tokens revoked on password change
    """
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), nullable=False)  # SHA-256 hash of token
    token_family = Column(String(36), nullable=False)  # Group related tokens for revocation
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)  # NULL if valid
    revoked_reason = Column(String(50), nullable=True)  # rotation, logout, security
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    device = relationship("Device", foreign_keys=[device_id])
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('ix_refresh_tokens_hash', 'token_hash'),
        Index('ix_refresh_tokens_device', 'device_id'),
        Index('ix_refresh_tokens_user', 'user_id'),
        Index('ix_refresh_tokens_family', 'token_family'),
    )

    @property
    def is_valid(self) -> bool:
        """Token is valid if not expired and not revoked."""
        if self.revoked_at:
            return False
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        return self.revoked_at is not None

    def revoke(self, reason: str = "rotation") -> None:
        """Revoke this token."""
        self.revoked_at = datetime.now(timezone.utc)
        self.revoked_reason = reason

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses (excludes sensitive data)."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_reason": self.revoked_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_valid": self.is_valid,
        }
