import os
import json
from datetime import datetime
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import logging
from starlette.concurrency import run_in_threadpool

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name__)

def get_credentials():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        error_message = "CRITICAL ERROR: Missing Google credentials in environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN)."
        logger.error(error_message)
        raise ValueError(error_message)

    logger.info("Found Google credentials in environment variables. Creating credentials.")
    
    creds = Credentials(
        token=None,  
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    creds.refresh(Request())
    
    return creds

# The rest of the file remains the same.
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
    if not service: return False
    body = {"timeMin": start_time.isoformat(), "timeMax": end_time.isoformat(), "items": [{"id": doctor_email}]}
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
    if not service: return None
    event = {'summary': summary, 'description': description, 'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'}, 'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'}, 'attendees': [{'email': email} for email in attendees] if attendees else []}
    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        logger.info(f"Event created: {event.get('htmlLink')}")
        return event.get('htmlLink')
    except HttpError as error:
        logger.error(f"Error creating calendar event: {error}")
        return None