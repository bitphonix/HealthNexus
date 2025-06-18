# backend/mcp_tools/doctor_tools.py
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.models import Doctor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolException(Exception):
    """Custom exception for tool-related errors."""
    pass

async def get_doctors_by_specialty(db: Session, specialty: str) -> dict:
    """
    Retrieves a list of doctors by their specialty.
    """
    try:
        if not specialty:
            raise ToolException("Specialty must be provided.")
        
        search_term = specialty
        if search_term.lower().endswith('ist'):
            search_term = search_term[:-3]
        
        doctors = db.query(Doctor).filter(Doctor.specialty.ilike(f"%{search_term}%")).all()

        if not doctors:
            return {"status": "success", "message": f"No doctors found with the specialty '{specialty}'."}

        doctor_details = [{"name": d.name, "email": d.email} for d in doctors]
        
        logger.info(f"Found {len(doctor_details)} doctors with specialty '{specialty}': {doctor_details}")
        return {
            "status": "success",
            "specialty": specialty,
            "doctors": doctor_details
        }
    except Exception as e:
        logger.error(f"An error occurred in get_doctors_by_specialty: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def get_doctor_details_by_name(db: Session, doctor_name: str) -> dict:
    """
    Retrieves the details (like specialty) for a single doctor by their name.
    """
    try:
        if not doctor_name:
            raise ToolException("Doctor name must be provided.")

        search_term = doctor_name.replace("Dr. ", "").strip()
        doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{search_term}%")).first()

        if not doctor:
            return {"status": "success", "message": f"No doctor found with the name '{doctor_name}'."}

        details = {
            "name": doctor.name,
            "specialty": doctor.specialty,
            "email": doctor.email
        }
        logger.info(f"Found details for {doctor_name}: {details}")
        return {"status": "success", "doctor_details": details}
    except Exception as e:
        logger.error(f"An error occurred in get_doctor_details_by_name: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}