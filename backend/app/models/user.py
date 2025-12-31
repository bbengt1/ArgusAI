"""User SQLAlchemy ORM model for authentication (Story P15-2.1)"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import validates, relationship
from app.core.database import Base
import uuid
from datetime import datetime, timezone
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User role enumeration for RBAC (Story P15-2.9)"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    """
    User model for multi-user authentication (Story P15-2.1)

    Attributes:
        id: UUID primary key
        username: Unique login username (3-50 chars, alphanumeric + underscore)
        email: Unique email address for login (optional, for future email invites)
        password_hash: bcrypt hash (cost factor 12)
        role: User role for RBAC (admin, operator, viewer)
        is_active: Whether account is enabled
        must_change_password: Force password change on next login
        password_expires_at: Expiry for temporary passwords (72h for invitations)
        created_at: Record creation timestamp (UTC)
        updated_at: Last modification timestamp (UTC)
        last_login: Last successful login timestamp (UTC)

    ADR-P15-002: Uses bcrypt with cost factor 12 (~250ms hash time)
    ADR-P15-003: Three-role RBAC (admin, operator, viewer)
    """

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)  # Optional, for future email invites
    password_hash = Column(String(60), nullable=False)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.VIEWER,
        index=True
    )
    is_active = Column(Boolean, default=True, nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    password_expires_at = Column(DateTime(timezone=True), nullable=True)  # For temporary passwords
    # Story P14-5.7: Add timezone=True for consistent UTC handling
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationship to Device (Story P11-2.4)
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")

    # Relationship to Session (Story P15-2.2)
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_users_active_role', 'is_active', 'role'),
    )

    @validates('username')
    def validate_username(self, key, value):
        """
        Validate username format

        Requirements:
        - 3-50 characters
        - Alphanumeric and underscore only
        """
        if not value:
            raise ValueError("Username is required")

        if len(value) < 3 or len(value) > 50:
            raise ValueError("Username must be 3-50 characters")

        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValueError("Username must contain only letters, numbers, and underscores")

        return value.lower()  # Normalize to lowercase

    @validates('email')
    def validate_email(self, key, value):
        """Validate email format if provided"""
        if value is None:
            return value

        value = value.strip().lower()
        if not value:
            return None

        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError("Invalid email format")

        if len(value) > 255:
            raise ValueError("Email must be 255 characters or less")

        return value

    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN

    def is_operator(self) -> bool:
        """Check if user has operator role"""
        return self.role == UserRole.OPERATOR

    def is_viewer(self) -> bool:
        """Check if user has viewer role"""
        return self.role == UserRole.VIEWER

    def can_manage_users(self) -> bool:
        """Check if user can manage other users (admin only)"""
        return self.is_admin()

    def can_manage_events(self) -> bool:
        """Check if user can manage events (admin, operator)"""
        return self.role in (UserRole.ADMIN, UserRole.OPERATOR)

    def password_is_expired(self) -> bool:
        """Check if temporary password has expired"""
        if self.password_expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.password_expires_at

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role.value}, active={self.is_active})>"
