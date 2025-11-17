"""
System Settings API

Endpoints for system-level configuration and monitoring:
    - Retention policy management (GET/PUT /retention)
    - Storage monitoring (GET /storage)
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from app.schemas.system import (
    RetentionPolicyUpdate,
    RetentionPolicyResponse,
    StorageResponse
)
from app.services.cleanup_service import get_cleanup_service
from app.core.database import get_db, SessionLocal
from app.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/system",
    tags=["system"]
)


def get_retention_policy_from_db(db: Optional[Session] = None) -> int:
    """
    Get current retention policy from system_settings table

    Args:
        db: Optional database session (creates new session if not provided)

    Returns:
        Retention days (default 30 if not set)
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        setting = db.query(SystemSetting).filter(
            SystemSetting.key == "data_retention_days"
        ).first()

        if setting and setting.value:
            try:
                return int(setting.value)
            except ValueError:
                logger.warning(f"Invalid retention policy value: {setting.value}, using default 30")
                return 30
        else:
            # Default: 30 days
            logger.info("No retention policy set, using default 30 days")
            return 30

    except Exception as e:
        logger.error(f"Error getting retention policy: {e}", exc_info=True)
        return 30
    finally:
        if should_close:
            db.close()


def set_retention_policy_in_db(retention_days: int, db: Optional[Session] = None):
    """
    Set retention policy in system_settings table

    Args:
        retention_days: Number of days to retain events
        db: Optional database session (creates new session if not provided)
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        setting = db.query(SystemSetting).filter(
            SystemSetting.key == "data_retention_days"
        ).first()

        if setting:
            setting.value = str(retention_days)
        else:
            setting = SystemSetting(
                key="data_retention_days",
                value=str(retention_days)
            )
            db.add(setting)

        db.commit()
        logger.info(f"Retention policy updated: {retention_days} days")

    except Exception as e:
        logger.error(f"Error setting retention policy: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update retention policy"
        )
    finally:
        if should_close:
            db.close()


def calculate_next_cleanup() -> Optional[str]:
    """
    Calculate next cleanup time (2:00 AM next day)

    Returns:
        ISO 8601 timestamp of next cleanup, or None if error
    """
    try:
        now = datetime.now(timezone.utc)
        # Next 2:00 AM
        next_cleanup = now.replace(hour=2, minute=0, second=0, microsecond=0)

        # If it's already past 2:00 AM today, go to tomorrow
        if now.hour >= 2:
            next_cleanup += timedelta(days=1)

        return next_cleanup.isoformat()

    except Exception as e:
        logger.error(f"Error calculating next cleanup: {e}", exc_info=True)
        return None


@router.get("/retention", response_model=RetentionPolicyResponse)
async def get_retention_policy(db: Session = Depends(get_db)):
    """
    Get current data retention policy

    Returns current retention policy configuration including:
    - Number of days events are retained
    - Whether retention is set to forever (retention_days <= 0)
    - Next scheduled cleanup time

    **Response:**
    ```json
    {
        "retention_days": 30,
        "next_cleanup": "2025-11-18T02:00:00Z",
        "forever": false
    }
    ```

    **Status Codes:**
    - 200: Success
    - 500: Internal server error
    """
    try:
        retention_days = get_retention_policy_from_db(db)
        forever = retention_days <= 0
        next_cleanup = calculate_next_cleanup() if not forever else None

        return RetentionPolicyResponse(
            retention_days=retention_days,
            next_cleanup=next_cleanup,
            forever=forever
        )

    except Exception as e:
        logger.error(f"Error getting retention policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve retention policy"
        )


@router.put("/retention", response_model=RetentionPolicyResponse)
async def update_retention_policy(
    policy: RetentionPolicyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update data retention policy

    Update how long events are retained before automatic cleanup.

    **Valid retention_days values:**
    - -1 or 0: Keep events forever (no automatic cleanup)
    - 7: Keep for 7 days
    - 30: Keep for 30 days (default)
    - 90: Keep for 90 days
    - 365: Keep for 1 year

    **Request Body:**
    ```json
    {
        "retention_days": 30
    }
    ```

    **Response:**
    ```json
    {
        "retention_days": 30,
        "next_cleanup": "2025-11-18T02:00:00Z",
        "forever": false
    }
    ```

    **Status Codes:**
    - 200: Success
    - 400: Invalid retention_days value
    - 500: Internal server error
    """
    try:
        # Validation is handled by Pydantic schema
        set_retention_policy_in_db(policy.retention_days, db)

        forever = policy.retention_days <= 0
        next_cleanup = calculate_next_cleanup() if not forever else None

        return RetentionPolicyResponse(
            retention_days=policy.retention_days,
            next_cleanup=next_cleanup,
            forever=forever
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating retention policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update retention policy"
        )


@router.get("/storage", response_model=StorageResponse)
async def get_storage_info():
    """
    Get storage usage information

    Returns detailed storage statistics including:
    - Database size (SQLite file size via PRAGMA queries)
    - Thumbnails directory size (recursive calculation)
    - Total storage used
    - Number of events stored

    **Response:**
    ```json
    {
        "database_mb": 15.2,
        "thumbnails_mb": 8.5,
        "total_mb": 23.7,
        "event_count": 1234
    }
    ```

    **Status Codes:**
    - 200: Success
    - 500: Internal server error
    """
    try:
        cleanup_service = get_cleanup_service()
        storage_info = await cleanup_service.get_storage_info()

        return StorageResponse(**storage_info)

    except Exception as e:
        logger.error(f"Error getting storage info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage information"
        )
