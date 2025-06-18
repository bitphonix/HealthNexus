# backend/mcp_tools/availability_tools.py
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import pytz

from backend.models import Doctor, DoctorAvailability
from backend.services.google_calendar import check_availability as gc_check_availability
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class ToolException(Exception): ...

async def check_doctor_availability(db: Session, doctor_name_or_email: str, target_date_str: Optional[str] = None) -> dict:
    try:
        search_term = doctor_name_or_email.replace("Dr. ", "").strip()
        doctor = db.query(Doctor).filter(or_(Doctor.name.ilike(f"%{search_term}%"), Doctor.email == doctor_name_or_email)).first()
        if not doctor:
            raise ToolException(f"Doctor '{doctor_name_or_email}' not found.")

        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date() if target_date_str else date.today()

        availabilities = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date == target_date,
            DoctorAvailability.is_booked == False
        ).order_by(DoctorAvailability.start_time).all()

        if not availabilities:
            return {"status": "success", "message": f"Dr. {doctor.name} has no scheduled availability on {target_date.strftime('%Y-%m-%d')}."}

        available_slots = []
        for slot in availabilities:
            start_time_aware = IST.localize(slot.start_time)
            end_time_aware = IST.localize(slot.end_time)
            
            if await gc_check_availability(doctor.email, start_time_aware, end_time_aware):
                available_slots.append(slot.start_time.strftime("%H:%M:%S")) # Append the string directly
        
        if not available_slots:
            return {"status": "success", "message": f"Dr. {doctor.name} has no available slots on {target_date.strftime('%Y-%m-%d')} after checking the calendar."}
        
        return {
            "status": "success", "doctor_name": doctor.name, "doctor_email": doctor.email,
            "date": target_date.strftime("%Y-%m-%d"), "available_slots": available_slots
        }
    except Exception as e:
        logger.error(f"An error in check_doctor_availability: {e}", exc_info=True)
        raise e
