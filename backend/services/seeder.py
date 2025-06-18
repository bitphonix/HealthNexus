# backend/services/seeder.py
from sqlalchemy.orm import Session
from faker import Faker
from datetime import datetime, timedelta, date
import random
import logging
import pytz 

from backend.database import SessionLocal, init_db
from backend.models import Doctor, Patient, DoctorAvailability, Appointment

fake = Faker()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

def seed_doctors(db: Session, num_doctors: int = 10):
    doctors = []
    
    predefined_doctor = Doctor(
        name="Dr. Evelyn Reed",
        specialty="Neurology",
        email="e.reed.neuro@clinic.com",
        phone_number="555-0101-2024"
    )
    exists = db.query(Doctor).filter(Doctor.email == predefined_doctor.email).first()
    if not exists:
        db.add(predefined_doctor)
        doctors.append(predefined_doctor)

    for _ in range(num_doctors - len(doctors)):
        doctor = Doctor(
            name=fake.name(),
            specialty=fake.random_element(elements=("Cardiology", "Pediatrics", "Dermatology", "Orthopedics", "General Practice")),
            email=fake.email(),
            phone_number=fake.phone_number()
        )
        db.add(doctor)
        doctors.append(doctor)
        
    db.commit()
    for doctor in doctors:
        db.refresh(doctor)
    logger.info(f"Seeded {len(doctors)} doctors, including a predefined Neurologist.")
    return db.query(Doctor).all()

def seed_patients(db: Session, num_patients: int = 20):
    patients = []
    for _ in range(num_patients):
        patient = Patient(
            name=fake.name(),
            email=fake.email(),
            phone_number=fake.phone_number(),
            condition=fake.random_element(elements=(None, "Flu", "Diabetes", "Hypertension", "Allergies", "Broken Arm"))
        )
        db.add(patient)
        patients.append(patient)
    db.commit()
    for patient in patients:
        db.refresh(patient)
    logger.info(f"Seeded {num_patients} patients.")
    return patients

def seed_doctor_availabilities(db: Session, doctors: list[Doctor], num_days: int = 7):
    availabilities = []
    for doctor in doctors:
        for i in range(num_days):
            current_date = date.today() + timedelta(days=i)
            for hour in [9, 11, 14, 16]:
                start_time = datetime(current_date.year, current_date.month, current_date.day, hour, 0, 0)
                end_time = start_time + timedelta(hours=1)
                availability = DoctorAvailability(
                    doctor_id=doctor.id,
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    is_booked=False
                )
                db.add(availability)
                availabilities.append(availability)
    db.commit()
    logger.info(f"Seeded availabilities for {len(doctors)} doctors over {num_days} days.")
    return availabilities

def seed_appointments(db: Session, doctors: list[Doctor], patients: list[Patient], availabilities: list[DoctorAvailability], num_appointments: int = 10):
    appointments = []
    random.shuffle(availabilities)
    for i in range(min(num_appointments, len(availabilities) // 2)):
        available_slot = availabilities[i]
        if not available_slot.is_booked:
            patient = random.choice(patients)
            
            aware_appointment_time = IST.localize(available_slot.start_time)
            
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=available_slot.doctor_id,
                appointment_time=aware_appointment_time, 
                reason=fake.sentence(nb_words=6),
                status="scheduled"
            )
            db.add(appointment)
            available_slot.is_booked = True
            appointments.append(appointment)
    db.commit()
    logger.info(f"Seeded {len(appointments)} appointments.")
    return appointments

def seed_all(db: Session):
    logger.info("Starting database seeding...")
    db.query(Appointment).delete()
    db.query(DoctorAvailability).delete()
    db.query(Patient).delete()
    db.query(Doctor).delete()
    db.commit()

    doctors = seed_doctors(db)
    patients = seed_patients(db)
    availabilities = seed_doctor_availabilities(db, doctors)
    
    logger.info("Database seeding completed. No fake appointments were created.")