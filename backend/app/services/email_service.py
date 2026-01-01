"""Email Service (Story P16-1.7)

Provides async email sending functionality using aiosmtplib.
Used for sending user invitation emails with temporary passwords.
"""
import logging
from typing import Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib
from sqlalchemy.orm import Session

from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    """SMTP configuration for email sending"""
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str = "ArgusAI"
    use_tls: bool = True
    use_starttls: bool = False


class EmailService:
    """
    Email service for sending notifications and invitations (Story P16-1.7)

    Features:
    - Async email sending via aiosmtplib
    - HTML email templates
    - SMTP configuration from settings
    - Support for TLS/STARTTLS
    """

    # Settings keys for SMTP configuration
    SMTP_HOST_KEY = "smtp_host"
    SMTP_PORT_KEY = "smtp_port"
    SMTP_USERNAME_KEY = "smtp_username"
    SMTP_PASSWORD_KEY = "smtp_password"  # encrypted
    SMTP_FROM_EMAIL_KEY = "smtp_from_email"
    SMTP_FROM_NAME_KEY = "smtp_from_name"
    SMTP_USE_TLS_KEY = "smtp_use_tls"
    SMTP_USE_STARTTLS_KEY = "smtp_use_starttls"
    SMTP_ENABLED_KEY = "smtp_enabled"

    def __init__(self, db: Session):
        self.db = db
        self.settings_service = SettingsService(db)

    def is_configured(self) -> bool:
        """Check if SMTP is configured and enabled"""
        enabled = self.settings_service.get_setting(self.SMTP_ENABLED_KEY)
        if enabled != "true":
            return False

        host = self.settings_service.get_setting(self.SMTP_HOST_KEY)
        return bool(host)

    def get_smtp_config(self) -> Optional[SMTPConfig]:
        """Get SMTP configuration from settings"""
        if not self.is_configured():
            return None

        host = self.settings_service.get_setting(self.SMTP_HOST_KEY)
        port_str = self.settings_service.get_setting(self.SMTP_PORT_KEY) or "587"
        username = self.settings_service.get_setting(self.SMTP_USERNAME_KEY) or ""
        password = self.settings_service.get_encrypted_setting(self.SMTP_PASSWORD_KEY) or ""
        from_email = self.settings_service.get_setting(self.SMTP_FROM_EMAIL_KEY) or ""
        from_name = self.settings_service.get_setting(self.SMTP_FROM_NAME_KEY) or "ArgusAI"
        use_tls = self.settings_service.get_setting(self.SMTP_USE_TLS_KEY) == "true"
        use_starttls = self.settings_service.get_setting(self.SMTP_USE_STARTTLS_KEY) == "true"

        return SMTPConfig(
            host=host,
            port=int(port_str),
            username=username,
            password=password,
            from_email=from_email,
            from_name=from_name,
            use_tls=use_tls,
            use_starttls=use_starttls,
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        config = self.get_smtp_config()
        if not config:
            logger.warning("SMTP not configured, cannot send email")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{config.from_name} <{config.from_email}>"
            msg["To"] = to_email

            # Add plain text part
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))

            # Add HTML part
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            if config.use_tls:
                # Direct TLS connection (port 465)
                await aiosmtplib.send(
                    msg,
                    hostname=config.host,
                    port=config.port,
                    username=config.username,
                    password=config.password,
                    use_tls=True,
                )
            else:
                # STARTTLS connection (port 587)
                await aiosmtplib.send(
                    msg,
                    hostname=config.host,
                    port=config.port,
                    username=config.username,
                    password=config.password,
                    start_tls=config.use_starttls,
                )

            logger.info(
                "Email sent successfully",
                extra={
                    "event_type": "email_sent",
                    "to": to_email,
                    "subject": subject,
                }
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send email: {e}",
                extra={
                    "event_type": "email_send_failed",
                    "to": to_email,
                    "subject": subject,
                    "error": str(e),
                }
            )
            return False

    async def send_invitation_email(
        self,
        to_email: str,
        username: str,
        temporary_password: str,
        login_url: str,
        invited_by: Optional[str] = None,
    ) -> bool:
        """
        Send user invitation email with credentials.

        Args:
            to_email: New user's email address
            username: New user's username
            temporary_password: Generated temporary password
            login_url: URL to the login page
            invited_by: Name of admin who sent the invitation

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Welcome to ArgusAI - Your Account Has Been Created"

        html_content = self._get_invitation_html(
            username=username,
            temporary_password=temporary_password,
            login_url=login_url,
            invited_by=invited_by,
        )

        text_content = self._get_invitation_text(
            username=username,
            temporary_password=temporary_password,
            login_url=login_url,
            invited_by=invited_by,
        )

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    def _get_invitation_html(
        self,
        username: str,
        temporary_password: str,
        login_url: str,
        invited_by: Optional[str] = None,
    ) -> str:
        """Generate HTML invitation email"""
        invited_text = f"You've been invited by {invited_by} to join ArgusAI." if invited_by else "You've been invited to join ArgusAI."

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to ArgusAI</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; border-bottom: 1px solid #e4e4e7;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #18181b;">
                                <span style="color: #2563eb;">Argus</span>AI
                            </h1>
                            <p style="margin: 8px 0 0; font-size: 14px; color: #71717a;">
                                AI-Powered Security Event Detection
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 16px; font-size: 20px; font-weight: 600; color: #18181b;">
                                Welcome to ArgusAI!
                            </h2>
                            <p style="margin: 0 0 24px; font-size: 16px; line-height: 1.6; color: #3f3f46;">
                                {invited_text}
                            </p>

                            <!-- Credentials Box -->
                            <div style="background-color: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                                <p style="margin: 0 0 12px; font-size: 14px; font-weight: 600; color: #92400e;">
                                    Your Login Credentials
                                </p>
                                <table role="presentation" style="width: 100%;">
                                    <tr>
                                        <td style="padding: 8px 0; font-size: 14px; color: #78350f;">
                                            <strong>Username:</strong>
                                        </td>
                                        <td style="padding: 8px 0; font-size: 14px; color: #78350f; font-family: monospace;">
                                            {username}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-size: 14px; color: #78350f;">
                                            <strong>Temporary Password:</strong>
                                        </td>
                                        <td style="padding: 8px 0; font-size: 14px; color: #78350f; font-family: monospace; background-color: #fef9c3; padding: 4px 8px; border-radius: 4px;">
                                            {temporary_password}
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Warning -->
                            <div style="background-color: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                                <p style="margin: 0; font-size: 13px; color: #991b1b;">
                                    <strong>Important:</strong> This temporary password expires in 72 hours. You will be required to change it on your first login.
                                </p>
                            </div>

                            <!-- CTA Button -->
                            <div style="text-align: center; margin: 32px 0;">
                                <a href="{login_url}" style="display: inline-block; padding: 14px 32px; background-color: #2563eb; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                                    Sign In to ArgusAI
                                </a>
                            </div>

                            <p style="margin: 0; font-size: 14px; color: #71717a; text-align: center;">
                                Or copy this URL: <a href="{login_url}" style="color: #2563eb; word-break: break-all;">{login_url}</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: #f4f4f5; border-radius: 0 0 12px 12px;">
                            <p style="margin: 0; font-size: 12px; color: #71717a; text-align: center;">
                                This email was sent by ArgusAI. If you did not expect this invitation, please ignore this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _get_invitation_text(
        self,
        username: str,
        temporary_password: str,
        login_url: str,
        invited_by: Optional[str] = None,
    ) -> str:
        """Generate plain text invitation email"""
        invited_text = f"You've been invited by {invited_by} to join ArgusAI." if invited_by else "You've been invited to join ArgusAI."

        return f"""
Welcome to ArgusAI!

{invited_text}

Your Login Credentials
----------------------
Username: {username}
Temporary Password: {temporary_password}

IMPORTANT: This temporary password expires in 72 hours. You will be required to change it on your first login.

Sign in at: {login_url}

---
This email was sent by ArgusAI. If you did not expect this invitation, please ignore this email.
"""

    async def test_connection(self) -> tuple[bool, str]:
        """
        Test SMTP connection without sending an email.

        Returns:
            Tuple of (success, message)
        """
        config = self.get_smtp_config()
        if not config:
            return False, "SMTP not configured"

        try:
            if config.use_tls:
                smtp = aiosmtplib.SMTP(
                    hostname=config.host,
                    port=config.port,
                    use_tls=True,
                )
            else:
                smtp = aiosmtplib.SMTP(
                    hostname=config.host,
                    port=config.port,
                )

            await smtp.connect()

            if config.use_starttls and not config.use_tls:
                await smtp.starttls()

            if config.username and config.password:
                await smtp.login(config.username, config.password)

            await smtp.quit()

            return True, "SMTP connection successful"

        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False, str(e)
