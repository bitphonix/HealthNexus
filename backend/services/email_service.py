# backend/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

load_dotenv()

GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str) -> bool:
    """Sends an email using Gmail SMTP. Requires a Gmail App Password."""
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        logger.error("GMAIL_SENDER or GMAIL_APP_PASSWORD not set in .env")
        return False

    logger.info(f"Attempting to send email to {to_email} with subject '{subject}'")
    msg = MIMEMultipart()
    msg['From'] = GMAIL_SENDER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Failed to send email to {to_email}: SMTP Authentication Error. Check your GMAIL_APP_PASSWORD. Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False