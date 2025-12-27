"""
Token Service (Stories P12-3.4, P12-3.5, P12-3.6)

Handles JWT token generation, refresh with rotation, and revocation.
"""
import logging
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.device import Device
from app.utils.jwt import create_access_token

logger = logging.getLogger(__name__)

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30
REFRESH_TOKEN_LENGTH = 64  # bytes
GRACE_PERIOD_SECONDS = 30  # Allow old token during rotation


class TokenService:
    """
    Service for managing mobile JWT tokens.

    Security features:
    - Refresh tokens stored as SHA-256 hashes
    - Token rotation on refresh (old token revoked)
    - Grace period for concurrent requests
    - Token family tracking for security events
    - Revocation on password change
    """

    def __init__(self, db: Session):
        self.db = db

    def create_token_pair(
        self,
        device_id: str,
        user_id: str,
    ) -> Tuple[str, str, int]:
        """
        Create a new access/refresh token pair.

        Args:
            device_id: Device UUID
            user_id: User UUID

        Returns:
            Tuple of (access_token, refresh_token, expires_in_seconds)
        """
        # Generate refresh token
        refresh_token = secrets.token_hex(REFRESH_TOKEN_LENGTH)
        token_hash = self._hash_token(refresh_token)
        token_family = str(uuid4())

        # Store refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_record = RefreshToken(
            device_id=device_id,
            user_id=user_id,
            token_hash=token_hash,
            token_family=token_family,
            expires_at=expires_at,
        )

        self.db.add(refresh_token_record)

        # Update device pairing status
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if device:
            device.pairing_confirmed = True
            device.update_last_seen()

        self.db.commit()

        # Generate access token
        access_token = create_access_token(
            data={"user_id": user_id, "device_id": device_id},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(
            "Token pair created",
            extra={
                "device_id": device_id,
                "user_id": user_id,
                "token_family": token_family,
            }
        )

        return access_token, refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def refresh_tokens(
        self,
        refresh_token: str,
        device_id: str,
    ) -> Optional[Tuple[str, str, int]]:
        """
        Refresh access token using refresh token with rotation.

        Args:
            refresh_token: Current refresh token
            device_id: Device UUID for validation

        Returns:
            Tuple of (access_token, new_refresh_token, expires_in) or None if invalid
        """
        token_hash = self._hash_token(refresh_token)

        # Find the refresh token
        token_record = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.device_id == device_id,
        ).first()

        if not token_record:
            logger.warning(
                "Refresh token not found",
                extra={"device_id": device_id}
            )
            return None

        # Check if token is valid
        if not token_record.is_valid:
            # Check if this is a recently revoked token (grace period)
            if token_record.revoked_at:
                grace_cutoff = datetime.now(timezone.utc) - timedelta(seconds=GRACE_PERIOD_SECONDS)
                if token_record.revoked_at > grace_cutoff:
                    # Within grace period, find the new token in the same family
                    new_token = self.db.query(RefreshToken).filter(
                        RefreshToken.token_family == token_record.token_family,
                        RefreshToken.revoked_at.is_(None),
                        RefreshToken.expires_at > datetime.now(timezone.utc),
                    ).first()

                    if new_token:
                        # Return the access token for the new refresh token
                        # (caller should still use their old refresh token)
                        access_token = create_access_token(
                            data={"user_id": token_record.user_id, "device_id": device_id},
                            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                        )
                        # Note: We return empty refresh_token to indicate no rotation needed
                        return access_token, "", ACCESS_TOKEN_EXPIRE_MINUTES * 60

            logger.warning(
                "Refresh token invalid",
                extra={
                    "device_id": device_id,
                    "revoked": token_record.is_revoked,
                    "expired": token_record.is_expired,
                }
            )
            return None

        # Revoke current token (rotation)
        token_record.revoke("rotation")

        # Generate new token pair with same family
        new_refresh_token = secrets.token_hex(REFRESH_TOKEN_LENGTH)
        new_token_hash = self._hash_token(new_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        new_token_record = RefreshToken(
            device_id=device_id,
            user_id=token_record.user_id,
            token_hash=new_token_hash,
            token_family=token_record.token_family,  # Keep same family
            expires_at=expires_at,
        )

        self.db.add(new_token_record)

        # Update device last seen
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if device:
            device.update_last_seen()

        self.db.commit()

        # Generate new access token
        access_token = create_access_token(
            data={"user_id": token_record.user_id, "device_id": device_id},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(
            "Token refreshed",
            extra={
                "device_id": device_id,
                "user_id": token_record.user_id,
                "token_family": token_record.token_family,
            }
        )

        return access_token, new_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def revoke_token(self, refresh_token: str, reason: str = "logout") -> bool:
        """
        Revoke a specific refresh token.

        Args:
            refresh_token: Token to revoke
            reason: Reason for revocation

        Returns:
            True if token was found and revoked
        """
        token_hash = self._hash_token(refresh_token)

        token_record = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        ).first()

        if not token_record:
            return False

        token_record.revoke(reason)
        self.db.commit()

        logger.info(
            "Token revoked",
            extra={
                "device_id": token_record.device_id,
                "reason": reason,
            }
        )

        return True

    def revoke_device_tokens(self, device_id: str, reason: str = "device_removed") -> int:
        """
        Revoke all tokens for a device.

        Args:
            device_id: Device UUID
            reason: Reason for revocation

        Returns:
            Number of tokens revoked
        """
        now = datetime.now(timezone.utc)

        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.device_id == device_id,
            RefreshToken.revoked_at.is_(None),
        ).all()

        for token in tokens:
            token.revoked_at = now
            token.revoked_reason = reason

        self.db.commit()

        logger.info(
            "Device tokens revoked",
            extra={
                "device_id": device_id,
                "count": len(tokens),
                "reason": reason,
            }
        )

        return len(tokens)

    def revoke_user_tokens(self, user_id: str, reason: str = "security") -> int:
        """
        Revoke all mobile tokens for a user (e.g., password change).

        Args:
            user_id: User UUID
            reason: Reason for revocation

        Returns:
            Number of tokens revoked
        """
        now = datetime.now(timezone.utc)

        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        ).all()

        for token in tokens:
            token.revoked_at = now
            token.revoked_reason = reason

        self.db.commit()

        logger.info(
            "User tokens revoked",
            extra={
                "user_id": user_id,
                "count": len(tokens),
                "reason": reason,
            }
        )

        return len(tokens)

    def cleanup_expired_tokens(self) -> int:
        """
        Delete expired and old revoked tokens.

        Returns:
            Number of tokens deleted
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        # Delete tokens that are both expired AND revoked > 7 days ago
        deleted = self.db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.now(timezone.utc),
            RefreshToken.revoked_at < cutoff,
        ).delete()

        self.db.commit()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old tokens")

        return deleted

    def _hash_token(self, token: str) -> str:
        """Hash a token using SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()
