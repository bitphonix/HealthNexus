# backend/services/slack_notifier.py
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_slack_message(message: str) -> bool:
    """
    Sends a message to Slack using a webhook URL.
    """
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL not set in .env")
        return False

    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        logger.info("Slack message sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack message: {e}")
        return False