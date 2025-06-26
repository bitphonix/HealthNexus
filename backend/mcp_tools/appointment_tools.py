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

    result = {
        "status": "success",
        "message": "",
        "appointment_id": None,
        "email_status": "not attempted",
        "calendar_event_link": "not attempted"
    }

    try:
        naive_appointment_time = datetime.strptime(appointment_time_str, "%Y-%m-%d %H:%M:%S")
        appointment_time_for_db = naive_appointment_time
        appointment_time = IST.localize(naive_appointment_time)
        end_time = appointment_time + timedelta(minutes=30)


        doctor = db.query(Doctor).filter(Doctor.email == doctor_email).first()
        if not doctor:
            result["status"] = "error"
            result["message"] = f"Doctor with email {doctor_email} not found."
            return result
        
        availability_slot = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.start_time == naive_appointment_time,
            DoctorAvailability.is_booked == False  
        ).first()

        if not availability_slot:
            return {"status": "error", "message": f"The requested time slot {appointment_time_str} is not available or already booked."}

        existing_appointment = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_time == appointment_time
        ).first()
        
        if existing_appointment:
            return {"status": "error", "message": f"An appointment already exists at {appointment_time_str}."}

        availability_slot.is_booked = True
        db.flush()  
        
        patient = db.query(Patient).filter(Patient.email == patient_email).first()
        if not patient:
            logger.warning(f"Patient with email {patient_email} not found. Creating a new patient.")
            patient = Patient(name=patient_email.split('@')[0], email=patient_email)
            db.add(patient)
            db.flush()  

        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_time=appointment_time_for_db,
            reason=reason,
            status="scheduled"
        )
        db.add(appointment)
        db.commit()  
        db.refresh(appointment)
        
        logger.info(f"Appointment created with ID: {appointment.id}")
        result["appointment_id"] = appointment.id
        result["message"] = "Appointment successfully created in database."

    except Exception as e:
        logger.error(f"Database error in book_appointment: {e}", exc_info=True)
        db.rollback()
        result["status"] = "error"
        result["message"] = f"Database error: {e}"
        return result

    try:
        email_subject = "Your Appointment Confirmation"
        email_body = f"Dear {patient.name},\n\nYour appointment with Dr. {doctor.name} on {appointment_time.strftime('%Y-%m-%d at %H:%M %Z')} is confirmed.\n\nAppointment ID: {appointment.id}"
        if await send_email(patient.email, email_subject, email_body):
            result["email_status"] = "Email sent successfully."
        else:
            result["email_status"] = "Email sending failed."
    except Exception as e:
        result["email_status"] = f"Email error: {e}"
        
    try:
        event_summary = f"Appointment: {patient.name} with Dr. {doctor.name}"
        event_description = f"Reason: {reason or 'N/A'}\nAppointment ID: {appointment.id}"
        calendar_link = await create_event(
            summary=event_summary, 
            description=event_description, 
            start_time=appointment_time,
            end_time=end_time, 
            attendees=[patient.email, doctor.email]
        )
        result["calendar_event_link"] = calendar_link or "Failed to create calendar event."
    except Exception as e:
        result["calendar_event_link"] = f"Calendar error: {e}"

    full_message = f"Appointment created with ID {result['appointment_id']}. Email: {result['email_status']}. Calendar: {result['calendar_event_link']}"
    result["message"] = full_message

    return result