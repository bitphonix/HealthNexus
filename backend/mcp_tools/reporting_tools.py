from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import func, cast, Date
import pytz

from backend.models import Appointment, Patient, Doctor
from backend.services.slack_notifier import send_slack_message
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class ToolException(Exception): ...


async def get_appointments_summary_for_doctor(db: Session, doctor_email: str, target_date_str: Optional[str] = None) -> dict:
    try:
        doctor = db.query(Doctor).filter(Doctor.email == doctor_email).first()
        if not doctor:
            raise ToolException(f"Doctor with email {doctor_email} not found.")

        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date() if target_date_str else date.today()

        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        start_of_day_ist = IST.localize(start_of_day)
        end_of_day_ist = IST.localize(end_of_day)

        appointments = db.query(Appointment).join(Patient).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_time >= start_of_day_ist,
            Appointment.appointment_time <= end_of_day_ist
        ).order_by(Appointment.appointment_time).all()

        doctor_name = doctor.name.replace("Dr. ", "").strip()

        if not appointments:
            message = f"Dr. {doctor_name} has no appointments scheduled for {target_date.strftime('%B %d, %Y')}."
            await send_slack_message(f"Daily Summary for Dr. {doctor_name}:\n{message}")
            return {"status": "success", "message": message}

        summary_lines = [f"Daily Appointment Summary for Dr. {doctor_name} ({target_date.strftime('%B %d, %Y')}):"]
        for i, appt in enumerate(appointments):
            if appt.appointment_time.tzinfo:
                appt_time_ist = appt.appointment_time.astimezone(IST)
            else:
                appt_time_ist = IST.localize(appt.appointment_time)
            
            if appt.patient:
                patient_name = appt.patient.name
                patient_email = appt.patient.email
            else:
                patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
                if patient:
                    patient_name = patient.name
                    patient_email = patient.email
                else:
                    patient_name = "Unknown Patient"
                    patient_email = "N/A"
                    logger.warning(f"Patient not found for appointment {appt.id} with patient_id {appt.patient_id}")
                
            summary_lines.append(
                f"{i+1}. Time: {appt_time_ist.strftime('%H:%M')} IST, "
                f"Patient: {patient_name} ({patient_email}), "
                f"Reason: {appt.reason or 'N/A'}, "
                f"ID: {appt.id}"
            )
        
        full_summary = "\n".join(summary_lines)
        await send_slack_message(full_summary)
        return {
            "status": "success", 
            "message": full_summary, 
            "appointment_count": len(appointments)
        }
    except Exception as e:
        logger.error(f"Error in get_appointments_summary_for_doctor: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    
async def get_patient_count_by_date(db: Session, target_date_str: str) -> dict:
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        patient_count = db.query(func.count(func.distinct(Appointment.patient_id))).filter(
            cast(Appointment.appointment_time.op('AT TIME ZONE')('Asia/Kolkata'), Date) == target_date
        ).scalar()
        message = f"On {target_date_str}, there are {patient_count} unique patients with appointments."
        logger.info(message)
        return {"status": "success", "message": message, "patient_count": patient_count}
    except ValueError:
        raise ToolException("Invalid date format. Please use YYYY-MM-DD.")
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}

async def get_patients_with_condition(db: Session, condition: str) -> dict:
    try:
        patients = db.query(Patient).filter(Patient.condition.ilike(f"%{condition}%")).all()
        if not patients:
            return {"status": "success", "message": f"No patients found with condition '{condition}'."}
        results = [{"patient_name": p.name, "patient_email": p.email, "condition": p.condition} for p in patients]
        return {"status": "success", "message": f"Found {len(results)} patients.", "patients": results}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}")