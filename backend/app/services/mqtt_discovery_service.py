"""
MQTT Discovery Service for Home Assistant Integration (Story P4-2.2)

Provides Home Assistant MQTT Discovery protocol support:
- Generate discovery configuration payloads for cameras
- Publish discovery configs on MQTT connect
- Remove sensors when cameras are deleted/disabled
- Track discovery state for republishing on reconnect

Uses Home Assistant MQTT Discovery protocol:
https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List

from app.services.mqtt_service import MQTTService, get_mqtt_service
from app.core.database import SessionLocal
from app.models.mqtt_config import MQTTConfig
from app.models.camera import Camera

logger = logging.getLogger(__name__)

# Application version for device info
APP_VERSION = "4.0.0"


class MQTTDiscoveryService:
    """
    Home Assistant MQTT Discovery service (Story P4-2.2).

    Manages automatic sensor registration in Home Assistant via MQTT Discovery.
    Creates sensor entities for each camera that publish AI event descriptions.

    Features:
    - Generate HA-compatible discovery payloads
    - Publish discovery on MQTT connect
    - Remove sensors on camera delete/disable
    - Support discovery enable/disable toggle

    Discovery Topic Format:
        {discovery_prefix}/sensor/liveobject_{camera_id}_event/config

    Sensor Payload Structure:
        - name: "{camera_name} AI Events"
        - unique_id: "liveobject_{camera_id}_event"
        - state_topic: "{topic_prefix}/camera/{camera_id}/event"
        - availability_topic: "{topic_prefix}/status"
        - device grouping with identifiers

    Attributes:
        _mqtt_service: Reference to MQTT service for publishing
        _published_cameras: Set of camera IDs with active discovery
    """

    def __init__(self, mqtt_service: Optional[MQTTService] = None):
        """
        Initialize discovery service.

        Args:
            mqtt_service: MQTT service instance (uses singleton if not provided)
        """
        self._mqtt_service = mqtt_service
        self._published_cameras: set = set()

    @property
    def mqtt_service(self) -> MQTTService:
        """Get MQTT service instance (lazy load singleton if needed)."""
        if self._mqtt_service is None:
            self._mqtt_service = get_mqtt_service()
        return self._mqtt_service

    def generate_sensor_config(
        self,
        camera: Camera,
        topic_prefix: str = "liveobject"
    ) -> Dict[str, Any]:
        """
        Generate Home Assistant discovery payload for a camera sensor (AC1, AC3).

        Creates a sensor configuration that will appear in Home Assistant
        with proper device grouping and state/attributes topics.

        Args:
            camera: Camera model instance
            topic_prefix: MQTT topic prefix (default "liveobject")

        Returns:
            Dictionary ready for JSON serialization to discovery topic.

        Example:
            >>> config = service.generate_sensor_config(camera)
            >>> mqtt.publish(discovery_topic, config)
        """
        camera_id = str(camera.id)

        # Build unique identifiers
        sensor_unique_id = f"liveobject_{camera_id}_event"
        device_identifier = f"liveobject_{camera_id}"

        # Build topics
        state_topic = f"{topic_prefix}/camera/{camera_id}/event"
        availability_topic = f"{topic_prefix}/status"

        # Determine camera type for model field
        camera_type = camera.source_type or camera.type
        if camera.is_doorbell:
            model_name = "AI Classifier - Doorbell"
        elif camera_type == "protect":
            model_name = "AI Classifier - Protect"
        elif camera_type == "usb":
            model_name = "AI Classifier - USB"
        else:
            model_name = "AI Classifier - RTSP"

        # Build discovery payload per HA MQTT Discovery spec
        config = {
            # Entity identification
            "name": f"{camera.name} AI Events",
            "unique_id": sensor_unique_id,
            "object_id": sensor_unique_id,

            # State and attributes
            "state_topic": state_topic,
            "value_template": "{{ value_json.description[:255] if value_json.description else 'No event' }}",
            "json_attributes_topic": state_topic,

            # Availability (AC7)
            "availability_topic": availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",

            # Icon based on camera type
            "icon": "mdi:doorbell-video" if camera.is_doorbell else "mdi:cctv",

            # Device grouping (AC3)
            "device": {
                "identifiers": [device_identifier],
                "name": camera.name,
                "manufacturer": "Live Object AI",
                "model": model_name,
                "sw_version": APP_VERSION,
            }
        }

        return config

    def get_discovery_topic(
        self,
        camera_id: str,
        discovery_prefix: str = "homeassistant"
    ) -> str:
        """
        Get the discovery topic for a camera sensor.

        Args:
            camera_id: Camera UUID
            discovery_prefix: HA discovery prefix (default "homeassistant")

        Returns:
            Full discovery topic path.

        Example:
            homeassistant/sensor/liveobject_abc123_event/config
        """
        sensor_id = f"liveobject_{camera_id}_event"
        return f"{discovery_prefix}/sensor/{sensor_id}/config"

    async def publish_discovery_config(
        self,
        camera: Camera,
        config: Optional[MQTTConfig] = None
    ) -> bool:
        """
        Publish discovery configuration for a single camera (AC1).

        Args:
            camera: Camera to publish discovery for
            config: MQTT configuration (loads from DB if not provided)

        Returns:
            True if published successfully, False otherwise.
        """
        # Load config if not provided
        if config is None:
            with SessionLocal() as db:
                config = db.query(MQTTConfig).first()

        if not config:
            logger.warning("Cannot publish discovery: no MQTT config")
            return False

        # Check discovery is enabled (AC6)
        if not config.discovery_enabled:
            logger.debug(f"Discovery disabled, skipping camera {camera.id}")
            return False

        # Check MQTT is connected
        if not self.mqtt_service.is_connected:
            logger.warning("Cannot publish discovery: MQTT not connected")
            return False

        # Generate payload
        payload = self.generate_sensor_config(
            camera,
            topic_prefix=config.topic_prefix
        )

        # Get discovery topic
        topic = self.get_discovery_topic(
            str(camera.id),
            discovery_prefix=config.discovery_prefix
        )

        # Publish with QoS 1 and retain=True per HA spec
        success = await self.mqtt_service.publish(
            topic=topic,
            payload=payload,
            qos=1,
            retain=True
        )

        if success:
            self._published_cameras.add(str(camera.id))
            logger.info(
                f"Published discovery config for camera {camera.name}",
                extra={
                    "event_type": "mqtt_discovery_published",
                    "camera_id": str(camera.id),
                    "camera_name": camera.name,
                    "topic": topic
                }
            )
        else:
            logger.warning(
                f"Failed to publish discovery for camera {camera.name}",
                extra={
                    "event_type": "mqtt_discovery_failed",
                    "camera_id": str(camera.id)
                }
            )

        return success

    async def publish_all_discovery_configs(self) -> int:
        """
        Publish discovery configs for all enabled cameras (AC1, AC5).

        Called on MQTT connect and reconnect to ensure all sensors
        are registered in Home Assistant.

        Returns:
            Number of cameras successfully published.
        """
        # Load MQTT config
        with SessionLocal() as db:
            config = db.query(MQTTConfig).first()

        if not config:
            logger.warning("No MQTT config found, skipping discovery")
            return 0

        # Check discovery is enabled (AC6)
        if not config.discovery_enabled:
            logger.info("MQTT discovery disabled, skipping all cameras")
            return 0

        # Get all enabled cameras
        with SessionLocal() as db:
            cameras = db.query(Camera).filter(Camera.is_enabled == True).all()

            if not cameras:
                logger.info("No enabled cameras found for discovery")
                return 0

            # Publish for each camera
            published_count = 0
            for camera in cameras:
                try:
                    if await self.publish_discovery_config(camera, config):
                        published_count += 1
                except Exception as e:
                    logger.error(
                        f"Error publishing discovery for camera {camera.id}: {e}",
                        extra={
                            "event_type": "mqtt_discovery_error",
                            "camera_id": str(camera.id),
                            "error": str(e)
                        }
                    )

            logger.info(
                f"Published discovery for {published_count}/{len(cameras)} cameras",
                extra={
                    "event_type": "mqtt_discovery_all_complete",
                    "published_count": published_count,
                    "total_cameras": len(cameras)
                }
            )

            return published_count

    async def remove_discovery_config(
        self,
        camera_id: str,
        config: Optional[MQTTConfig] = None
    ) -> bool:
        """
        Remove discovery config for a camera (AC4).

        Publishes empty payload to discovery topic to remove the sensor
        from Home Assistant.

        Args:
            camera_id: Camera UUID to remove
            config: MQTT configuration (loads from DB if not provided)

        Returns:
            True if removal published, False otherwise.
        """
        # Load config if not provided
        if config is None:
            with SessionLocal() as db:
                config = db.query(MQTTConfig).first()

        if not config:
            logger.warning("Cannot remove discovery: no MQTT config")
            return False

        # Check MQTT is connected
        if not self.mqtt_service.is_connected:
            logger.debug(f"MQTT not connected, cannot remove discovery for {camera_id}")
            # Still remove from tracking set
            self._published_cameras.discard(camera_id)
            return False

        # Get discovery topic
        topic = self.get_discovery_topic(
            camera_id,
            discovery_prefix=config.discovery_prefix
        )

        # Publish empty payload to remove sensor (HA Discovery spec)
        # Note: Empty string payload with retain=True removes the retained message
        try:
            if self.mqtt_service._client:
                result = self.mqtt_service._client.publish(
                    topic,
                    payload="",
                    qos=1,
                    retain=True
                )

                if result.rc == 0:
                    self._published_cameras.discard(camera_id)
                    logger.info(
                        f"Removed discovery config for camera {camera_id}",
                        extra={
                            "event_type": "mqtt_discovery_removed",
                            "camera_id": camera_id,
                            "topic": topic
                        }
                    )
                    return True

        except Exception as e:
            logger.error(
                f"Error removing discovery for camera {camera_id}: {e}",
                extra={
                    "event_type": "mqtt_discovery_remove_error",
                    "camera_id": camera_id,
                    "error": str(e)
                }
            )

        return False

    async def remove_all_discovery_configs(self) -> int:
        """
        Remove all discovery configs (AC6: when discovery disabled).

        Returns:
            Number of cameras removed.
        """
        # Load config for prefix
        with SessionLocal() as db:
            config = db.query(MQTTConfig).first()

        if not config:
            return 0

        # Get list of published cameras
        cameras_to_remove = list(self._published_cameras)

        removed_count = 0
        for camera_id in cameras_to_remove:
            if await self.remove_discovery_config(camera_id, config):
                removed_count += 1

        logger.info(
            f"Removed discovery for {removed_count} cameras",
            extra={
                "event_type": "mqtt_discovery_all_removed",
                "removed_count": removed_count
            }
        )

        return removed_count

    def on_mqtt_connect(self) -> None:
        """
        Callback for MQTT connection (AC5: discovery on reconnect).

        Called by MQTTService when connection is established.
        Triggers discovery publishing for all cameras.
        """
        logger.info(
            "MQTT connected, publishing discovery configs",
            extra={"event_type": "mqtt_discovery_connect_trigger"}
        )

        # Schedule async publish in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._publish_discovery_on_connect())
            else:
                loop.run_until_complete(self._publish_discovery_on_connect())
        except RuntimeError:
            # No event loop, try to create one
            asyncio.run(self._publish_discovery_on_connect())

    async def _publish_discovery_on_connect(self) -> None:
        """Internal async handler for on_connect callback."""
        try:
            # Small delay to ensure connection is stable
            await asyncio.sleep(0.5)

            # Publish online status first (AC7)
            await self._publish_online_status()

            # Then publish all discovery configs
            await self.publish_all_discovery_configs()

        except Exception as e:
            logger.error(
                f"Error publishing discovery on connect: {e}",
                extra={"event_type": "mqtt_discovery_connect_error", "error": str(e)}
            )

    async def _publish_online_status(self) -> None:
        """Publish online status to availability topic (AC7)."""
        with SessionLocal() as db:
            config = db.query(MQTTConfig).first()

        if not config:
            return

        status_topic = f"{config.topic_prefix}/status"

        # Publish "online" to status topic
        try:
            if self.mqtt_service._client:
                self.mqtt_service._client.publish(
                    status_topic,
                    payload="online",
                    qos=1,
                    retain=True
                )
                logger.debug(
                    f"Published online status to {status_topic}",
                    extra={"event_type": "mqtt_status_online"}
                )
        except Exception as e:
            logger.error(f"Failed to publish online status: {e}")


# Global singleton instance
_discovery_service: Optional[MQTTDiscoveryService] = None


def get_discovery_service() -> MQTTDiscoveryService:
    """
    Get the global MQTT discovery service instance.

    Returns:
        MQTTDiscoveryService singleton instance.
    """
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = MQTTDiscoveryService()
    return _discovery_service


async def initialize_discovery_service() -> None:
    """
    Initialize discovery service and register with MQTT service.

    Called during app startup after MQTT service is initialized.
    """
    discovery = get_discovery_service()
    mqtt = get_mqtt_service()

    # Register on_connect callback for discovery publishing (AC5)
    mqtt.set_on_connect_callback(discovery.on_mqtt_connect)

    logger.info(
        "MQTT discovery service initialized",
        extra={"event_type": "mqtt_discovery_init"}
    )


async def on_camera_deleted(camera_id: str) -> None:
    """
    Hook for camera deletion - removes discovery config (AC4).

    Call this from camera delete flow.

    Args:
        camera_id: UUID of deleted camera
    """
    discovery = get_discovery_service()
    await discovery.remove_discovery_config(camera_id)


async def on_camera_disabled(camera_id: str) -> None:
    """
    Hook for camera disable - removes discovery config (AC4).

    Call this from camera disable flow.

    Args:
        camera_id: UUID of disabled camera
    """
    discovery = get_discovery_service()
    await discovery.remove_discovery_config(camera_id)


async def on_discovery_setting_changed(enabled: bool) -> None:
    """
    Hook for discovery_enabled setting change (AC6).

    Args:
        enabled: New discovery_enabled value
    """
    discovery = get_discovery_service()

    if enabled:
        # Re-publish all discovery configs
        await discovery.publish_all_discovery_configs()
    else:
        # Remove all discovery configs
        await discovery.remove_all_discovery_configs()
