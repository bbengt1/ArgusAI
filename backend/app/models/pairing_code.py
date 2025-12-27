"""
PairingCode Model (Story P12-3.1)

Temporary pairing codes for mobile device authentication.
Codes expire after 5 minutes and are deleted after use.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class PairingCode(Base):
    """
    Temporary pairing codes for mobile device authentication.

    Flow:
    1. Mobile app requests pairing code
    2. User enters code in web dashboard
    3. Server confirms code, associates with user
    4. Mobile app exchanges confirmed code for tokens
    5. Code is deleted after use
    """
    __tablename__ = "pairing_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(6), unique=True, nullable=False)  # 6-digit code
    device_id = Column(String(255), nullable=False)  # Hardware device ID
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # NULL until confirmed
    platform = Column(String(20), nullable=False)  # ios, android
    device_name = Column(String(100), nullable=True)  # User-friendly name
    device_model = Column(String(100), nullable=True)  # Device hardware model
    expires_at = Column(DateTime(timezone=True), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('ix_pairing_codes_code', 'code'),
        Index('ix_pairing_codes_expires', 'expires_at'),
        Index('ix_pairing_codes_device', 'device_id'),
    )

    @property
    def is_expired(self) -> bool:
        """Check if code has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_confirmed(self) -> bool:
        """Check if code has been confirmed by user."""
        return self.confirmed_at is not None

    @property
    def is_valid_for_exchange(self) -> bool:
        """Check if code is ready for token exchange."""
        return self.is_confirmed and not self.is_expired

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "code": self.code,
            "device_id": self.device_id,
            "platform": self.platform,
            "device_name": self.device_name,
            "device_model": self.device_model,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_expired": self.is_expired,
            "is_confirmed": self.is_confirmed,
        }
