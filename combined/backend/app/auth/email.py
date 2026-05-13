"""Email delivery for OTPs.

If SMTP_HOST is configured we send via aiosmtplib; otherwise we log the OTP
to stdout so development never blocks.
"""
from __future__ import annotations

from email.message import EmailMessage

from app.core.config import settings
from app.telemetry.logger import get_logger

log = get_logger(__name__)


async def send_otp_email(to: str, code: str) -> None:
    subject = f"{settings.APP_NAME} login code"
    body = (
        f"Your {settings.APP_NAME} verification code is:\n\n"
        f"    {code}\n\n"
        f"This code expires in {settings.OTP_TTL_SECONDS // 60} minutes.\n"
        "If you did not request this, you can safely ignore this email.\n"
    )

    if not settings.SMTP_HOST:
        log.info("otp_dev_delivery", extra={"to": to, "code": code})
        return

    try:
        import aiosmtplib  # type: ignore

        msg = EmailMessage()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_TLS,
            timeout=10,
        )
        log.info("otp_email_sent", extra={"to": to})
    except Exception as exc:  # noqa: BLE001
        log.warning("otp_email_failed", extra={"to": to, "err": str(exc)[:200]})
