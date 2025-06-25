from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import pytz
import logging

from backend.models import Appointment, Doctor, Patient, DoctorAvailability
from backend.services.google_calendar import create_event
from backend.services.email_service import send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class ToolException(Exception):
    pass

async def book_appointment(
    db: Session,
    patient_email: str,
    doctor_email: str,
    appointment_time_str: str,
    reason: Optional[str] = None
) -> dict:
    
    naive_appointment_time = datetime.strptime(appointment_time_str, "%Y-%m-%d %H:%M:%S")
    appointment_time = IST.localize(naive_appointment_time)
    end_time = appointment_time + timedelta(minutes=30)

    doctor = db.query(Doctor).filter(Doctor.email == doctor_email).first()
    if not doctor:
        return {"status": "error", "message": f"Doctor with email {doctor_email} not found."}

    availability_slot = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.start_time == naive_appointment_time
    ).first()

    if not availability_slot or availability_slot.is_booked:
        return {"status": "error", "message": f"Sorry, the requested time slot {appointment_time_str} is not available."}

    availability_slot.is_booked = True

    patient = db.query(Patient).filter(Patient.email == patient_email).first()
    if not patient:
        logger.warning(f"Patient with email {patient_email} not found. Creating a new patient.")
        patient = Patient(name=patient_email.split('@')[0], email=patient_email)
        db.add(patient)

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_time=appointment_time,
        reason=reason,
        status="scheduled"
    )
    db.add(appointment)
    
    db.flush()
    appointment_id = appointment.id
    logger.info(f"Staged appointment with ID: {appointment_id} and updated availability slot.")

    email_sent = await send_email(
        to_email=patient.email,
        subject="Your Appointment Confirmation",
        body=f"Dear {patient.name},\n\nYour appointment with Dr. {doctor.name} on {appointment_time.strftime('%Y-%m-%d at %H:%M %Z')} is confirmed."
    )
    
    calendar_link = await create_event(
        summary=f"Appointment: {patient.name} with Dr. {doctor.name}",
        description=f"Reason: {reason or 'N/A'}",
        start_time=appointment_time,
        end_time=end_time,
        attendees=[patient.email, doctor.email]
    )

    return {
        "status": "success",
        "message": f"Appointment created with ID {appointment_id}. Email status: {'Sent' if email_sent else 'Failed'}. Calendar status: {'Created' if calendar_link else 'Failed'}.",
        "appointment_id": appointment_id,
        "email_status": "Email sent successfully." if email_sent else "Email sending failed.",
        "calendar_event_link": calendar_link or "Failed to create calendar event."
    }