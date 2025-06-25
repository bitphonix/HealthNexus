# backend/services/seeder.py

from sqlalchemy.orm import Session
from faker import Faker
from datetime import datetime, timedelta, date
import logging
import pytz

from backend.database import init_db
from backend.models import Doctor, Patient, DoctorAvailability, Appointment

fake = Faker()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

def seed_doctors(db: Session):
    predefined_doctor_email = "e.reed.neuro@clinic.com"
    exists = db.query(Doctor).filter(Doctor.email == predefined_doctor_email).first()
    
    if not exists:
        predefined_doctor = Doctor(
            name="Dr. Evelyn Reed",
            specialty="Neurology",
            email=predefined_doctor_email,
            phone_number="555-0101-2024"
        )
        db.add(predefined_doctor)
        logger.info("Created predefined Neurologist: Dr. Evelyn Reed.")
        db.commit()

def seed_availabilities(db: Session, num_days: int = 7):
    logger.info("Refreshing doctor availability schedule...")
    
    all_doctors = db.query(Doctor).all()
    if not all_doctors:
        logger.warning("No doctors found in the database to seed availabilities for.")
        return

    future_appointments = db.query(Appointment).filter(
        Appointment.appointment_time >= datetime.now(pytz.utc)
    ).all()
    
    booked_slots = set()
    for appt in future_appointments:
        naive_ist_time = appt.appointment_time.astimezone(IST).replace(tzinfo=None)
        booked_slots.add((appt.doctor_id, naive_ist_time))
    
    db.query(DoctorAvailability).delete()
        
    new_availability_slots = []
    for doctor in all_doctors:
        for i in range(num_days):
            current_date = date.today() + timedelta(days=i)
            for hour in [9, 11, 14, 16]:
                start_time = datetime(current_date.year, current_date.month, current_date.day, hour, 0, 0)
                is_slot_booked = (doctor.id, start_time) in booked_slots
                
                new_slot = DoctorAvailability(
                    doctor_id=doctor.id,
                    date=current_date,
                    start_time=start_time,
                    end_time=start_time + timedelta(hours=1),
                    is_booked=is_slot_booked
                )
                new_availability_slots.append(new_slot)

    db.add_all(new_availability_slots)
    db.commit()
    logger.info(f"Refreshed availability for {len(all_doctors)} doctors, preserving {len(booked_slots)} existing bookings.")


def seed_all(db: Session):
    logger.info("Running smart seeder...")
    seed_doctors(db)
    seed_availabilities(db)
    logger.info("Seeding process complete. User data has been preserved.")