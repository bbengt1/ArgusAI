"""
UniFi Protect Service for controller connection management

Provides functionality to:
- Test controller connections before saving
- Manage WebSocket connections for real-time events (future stories)
- Discover cameras from connected controllers (future stories)
"""
import asyncio
import ssl
import logging
from typing import Optional
from dataclasses import dataclass

import aiohttp
from uiprotect import ProtectApiClient
from uiprotect.exceptions import BadRequest, NotAuthorized, NvrError

logger = logging.getLogger(__name__)

# Connection timeout in seconds (NFR3)
CONNECTION_TIMEOUT = 10.0


@dataclass
class ConnectionTestResult:
    """Result of a controller connection test"""
    success: bool
    message: str
    firmware_version: Optional[str] = None
    camera_count: Optional[int] = None
    error_type: Optional[str] = None


class ProtectService:
    """
    Service class for UniFi Protect controller operations.

    Handles connection testing, validation, and management of
    UniFi Protect controllers.
    """

    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        verify_ssl: bool = False
    ) -> ConnectionTestResult:
        """
        Test connection to a UniFi Protect controller.

        Attempts to connect to the controller, authenticate, and retrieve
        basic information (firmware version, camera count).

        Args:
            host: Controller IP address or hostname
            port: HTTPS port (default 443)
            username: Protect authentication username
            password: Protect authentication password
            verify_ssl: Whether to verify SSL certificates

        Returns:
            ConnectionTestResult with success status and details

        Note:
            This method does not persist any data - test-only operation.
            Connection is closed after test regardless of outcome.
        """
        # Log connection attempt (no credentials)
        logger.info(
            f"Testing Protect controller connection",
            extra={
                "event_type": "protect_connection_test_start",
                "host": host,
                "port": port,
                "verify_ssl": verify_ssl
            }
        )

        client = None
        try:
            # Create client with SSL verification setting
            client = ProtectApiClient(
                host=host,
                port=port,
                username=username,
                password=password,
                verify_ssl=verify_ssl
            )

            # Attempt connection with timeout
            await asyncio.wait_for(
                client.update(),
                timeout=CONNECTION_TIMEOUT
            )

            # Extract controller info
            firmware_version = None
            camera_count = 0

            if client.bootstrap:
                if client.bootstrap.nvr:
                    firmware_version = client.bootstrap.nvr.version
                camera_count = len(client.bootstrap.cameras) if client.bootstrap.cameras else 0

            logger.info(
                f"Protect controller connection successful",
                extra={
                    "event_type": "protect_connection_test_success",
                    "host": host,
                    "firmware_version": firmware_version,
                    "camera_count": camera_count
                }
            )

            return ConnectionTestResult(
                success=True,
                message="Connected successfully",
                firmware_version=firmware_version,
                camera_count=camera_count
            )

        except asyncio.TimeoutError:
            logger.warning(
                f"Protect controller connection timed out",
                extra={
                    "event_type": "protect_connection_test_timeout",
                    "host": host,
                    "timeout_seconds": CONNECTION_TIMEOUT
                }
            )
            return ConnectionTestResult(
                success=False,
                message=f"Connection timed out after {int(CONNECTION_TIMEOUT)} seconds",
                error_type="timeout"
            )

        except NotAuthorized:
            logger.warning(
                f"Protect controller authentication failed",
                extra={
                    "event_type": "protect_connection_test_auth_failed",
                    "host": host
                }
            )
            return ConnectionTestResult(
                success=False,
                message="Authentication failed",
                error_type="auth_error"
            )

        except aiohttp.ClientConnectorCertificateError as e:
            logger.warning(
                f"Protect controller SSL certificate error",
                extra={
                    "event_type": "protect_connection_test_ssl_error",
                    "host": host,
                    "error_type": "ssl_certificate"
                }
            )
            return ConnectionTestResult(
                success=False,
                message="SSL certificate verification failed",
                error_type="ssl_error"
            )

        except ssl.SSLError as e:
            logger.warning(
                f"Protect controller SSL error",
                extra={
                    "event_type": "protect_connection_test_ssl_error",
                    "host": host,
                    "error_type": "ssl"
                }
            )
            return ConnectionTestResult(
                success=False,
                message="SSL certificate verification failed",
                error_type="ssl_error"
            )

        except aiohttp.ClientConnectorError as e:
            logger.warning(
                f"Protect controller host unreachable",
                extra={
                    "event_type": "protect_connection_test_unreachable",
                    "host": host
                }
            )
            return ConnectionTestResult(
                success=False,
                message=f"Host unreachable: {host}",
                error_type="connection_error"
            )

        except (BadRequest, NvrError) as e:
            logger.warning(
                f"Protect controller error",
                extra={
                    "event_type": "protect_connection_test_error",
                    "host": host,
                    "error_type": type(e).__name__
                }
            )
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {type(e).__name__}",
                error_type="nvr_error"
            )

        except Exception as e:
            logger.error(
                f"Protect controller unexpected error",
                extra={
                    "event_type": "protect_connection_test_error",
                    "host": host,
                    "error_type": type(e).__name__
                }
            )
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {type(e).__name__}",
                error_type="unknown"
            )

        finally:
            # Always close the client connection
            if client:
                try:
                    await client.close()
                except Exception:
                    pass  # Ignore errors during cleanup


# Singleton instance for the service
_protect_service: Optional[ProtectService] = None


def get_protect_service() -> ProtectService:
    """Get the singleton ProtectService instance."""
    global _protect_service
    if _protect_service is None:
        _protect_service = ProtectService()
    return _protect_service
