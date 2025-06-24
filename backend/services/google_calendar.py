# backend/services/google_calendar.py
import os
from datetime import datetime
import pytz
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import logging
from starlette.concurrency import run_in_threadpool

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CREDENTIALS_PATH = "google_creds_v2.json"
TOKEN_PATH = "token.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_credentials():
    creds = None
    token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json_str:
        logger.info("Found token in environment variable. Loading credentials from it.")
        token_info = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    elif os.path.exists(TOKEN_PATH):
        logger.info("Found local token.json file. Loading credentials from it.")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.info("No valid credentials found. Starting local server for authentication.")
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds


async def get_calendar_service():
    try:
        creds = await run_in_threadpool(get_credentials)
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Google Calendar service initialized successfully.")
        return service
    except Exception as e:
        logger.error(f"Failed to get Google Calendar service: {e}", exc_info=True)
        return None

async def check_availability(doctor_email: str, start_time: datetime, end_time: datetime) -> bool:
    service = await get_calendar_service()
    if not service:
        return False
    body = {
        "timeMin": start_time.isoformat(),
        "timeMax": end_time.isoformat(),
        "items": [{"id": doctor_email}]
    }
    try:
        response = service.freebusy().query(body=body).execute()
        calendars = response.get('calendars', {})
        if doctor_email in calendars:
            busy_periods = calendars[doctor_email].get('busy', [])
            return not busy_periods
        return True
    except HttpError as error:
        logger.error(f"Error checking doctor availability for {doctor_email}: {error}")
        return False

async def create_event(summary: str, description: str, start_time: datetime, end_time: datetime, attendees: list[str] = None, calendar_id: str = 'primary'):
    service = await get_calendar_service()
    if not service:
        return None
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
        'attendees': [{'email': email} for email in attendees] if attendees else [],
        'reminders': {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 24 * 60}, {'method': 'popup', 'minutes': 10}]},
    }
    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        logger.info(f"Event created: {event.get('htmlLink')}")
        return event.get('htmlLink')
    except HttpError as error:
        logger.error(f"Error creating calendar event: {error}")
        return None