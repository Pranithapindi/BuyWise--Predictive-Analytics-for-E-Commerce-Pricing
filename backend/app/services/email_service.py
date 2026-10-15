"""
Email Service — sends price alert and welcome emails using aiosmtplib.
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from loguru import logger

from app.core.config import settings


async def send_email(to: str, subject: str, html_body: str):
    """Send a single HTML email."""
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.SMTP_USER}>"
        message["To"] = to
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"📧 Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")


async def send_welcome_email(email: str, username: str):
    """Send welcome email to newly registered user."""
    html = f"""
    <html><body style="font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px;">
      <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 40px;">
        <h1 style="color: #6366f1;">Welcome to PriceTracker! 🎉</h1>
        <p>Hi <strong>{username}</strong>,</p>
        <p>Your account has been created. Start tracking prices from Amazon, Flipkart, Myntra and more!</p>
        <a href="http://localhost:5173/dashboard"
           style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px;
                  border-radius: 8px; text-decoration: none; margin-top: 16px;">
          Go to Dashboard →
        </a>
        <p style="margin-top: 24px; color: #94a3b8; font-size: 12px;">
          © 2024 PriceTracker. All rights reserved.
        </p>
      </div>
    </body></html>
    """
    await send_email(email, "Welcome to PriceTracker! 🎉", html)


async def send_price_alert_email(
    email: str,
    product_id: str,
    current_price: float,
    target_price: Optional[float] = None,
):
    """Send a price drop alert email."""
    target_str = f"₹{target_price:.0f}" if target_price else "your target"
    html = f"""
    <html><body style="font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px;">
      <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 40px;">
        <h1 style="color: #22c55e;">🔔 Price Alert Triggered!</h1>
        <p>The price has dropped to <strong style="color: #22c55e; font-size: 24px;">₹{current_price:.0f}</strong></p>
        <p>This has reached {target_str}!</p>
        <a href="http://localhost:5173/products/{product_id}"
           style="display: inline-block; background: #22c55e; color: white; padding: 12px 24px;
                  border-radius: 8px; text-decoration: none; margin-top: 16px;">
          View Product →
        </a>
        <p style="margin-top: 24px; color: #94a3b8; font-size: 12px;">
          © 2024 PriceTracker. You set this alert. Manage alerts in your dashboard.
        </p>
      </div>
    </body></html>
    """
    await send_email(email, f"🔔 Price Alert: Now ₹{current_price:.0f}!", html)


async def send_password_reset_email(email: str, reset_token: str):
    """Send password reset link."""
    reset_url = f"http://localhost:5173/reset-password?token={reset_token}"
    html = f"""
    <html><body style="font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px;">
      <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 40px;">
        <h1 style="color: #f59e0b;">🔑 Password Reset</h1>
        <p>You requested a password reset. Click below to reset your password.</p>
        <p><strong>This link expires in 1 hour.</strong></p>
        <a href="{reset_url}"
           style="display: inline-block; background: #f59e0b; color: white; padding: 12px 24px;
                  border-radius: 8px; text-decoration: none; margin-top: 16px;">
          Reset Password →
        </a>
      </div>
    </body></html>
    """
    await send_email(email, "Password Reset Request", html)
