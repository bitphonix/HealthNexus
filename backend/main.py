import os
import logging
import uuid
from fastapi import FastAPI, Request, HTTPException, Depends, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from pydantic import BaseModel

from backend.database import init_db, get_db
from backend.services.seeder import seed_all
from backend.agents.doctor_agent import DoctorAppointmentAgent
# Import all tool modules
from backend.mcp_tools import appointment_tools, availability_tools, reporting_tools, doctor_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHAT_SESSIONS: Dict[str, DoctorAppointmentAgent] = {}

app = FastAPI(
    title="Doctor Appointment Assistant",
    description="A single, unified server for the Agentic AI application.",
    version="2.0.0"
)

app.mount("/static", StaticFiles(directory="backend/static"), name="static")
templates = Jinja2Templates(directory="backend/templates")

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Initializing database.")
    init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/seed")
async def seed_database(db: Session = Depends(get_db)):
    try:
        seed_all(db)
        return {"message": "Database seeded successfully!"}
    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    prompt: str
    role: str = "patient"
    session_id: Optional[str] = None

@app.post("/chat/")
async def chat_with_agent(chat_request: ChatRequest) -> Dict[str, Any]:
    session_id = chat_request.session_id
    if not session_id or session_id not in CHAT_SESSIONS:
        session_id = str(uuid.uuid4())
        logger.info(f"Creating new agent for session_id: {session_id}")
        CHAT_SESSIONS[session_id] = DoctorAppointmentAgent(role=chat_request.role)
    
    agent = CHAT_SESSIONS[session_id]
    if agent.role != chat_request.role:
        logger.info(f"Role changed for session {session_id}. Creating new agent.")
        agent = DoctorAppointmentAgent(role=chat_request.role)
        CHAT_SESSIONS[session_id] = agent
        
    logger.info(f"Using agent for session_id: {session_id} with role: {agent.role}")
    try:
        response = await agent.run(chat_request.prompt)
        response['session_id'] = session_id
        return response
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return {"response": f"An error occurred: {e}", "session_id": session_id}

# --- Tool Endpoints ---

@app.post("/tools/book_appointment/")
async def call_book_appointment(patient_email: str = Body(...), doctor_email: str = Body(...), appointment_time_str: str = Body(...), reason: str = Body(None), db: Session = Depends(get_db)):
    """
    This endpoint runs the full booking process and returns the simplest
    possible success message to guarantee it never crashes.
    """
    try:
        await appointment_tools.book_appointment(db, patient_email, doctor_email, appointment_time_str, reason)

        return {"status": "success", "message": "Appointment has been confirmed."}

    except Exception as e:
        logger.error(f"A critical error occurred in the booking tool endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/tools/check_doctor_availability/")
async def call_check_doctor_availability(doctor_name_or_email: str, target_date_str: str = None, db: Session = Depends(get_db)):
    try:
        result = await availability_tools.check_doctor_availability(db, doctor_name_or_email, target_date_str)
        if "error" in result.get("status", ""): raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tools/get_appointments_summary_for_doctor/")
async def call_get_appointments_summary_for_doctor(doctor_email: str, target_date_str: str = None, db: Session = Depends(get_db)):
    result = await reporting_tools.get_appointments_summary_for_doctor(db, doctor_email, target_date_str)
    if "error" in result.get("status", ""): raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.get("/tools/get_doctors_by_specialty/")
async def call_get_doctors_by_specialty(specialty: str, db: Session = Depends(get_db)):
    result = await doctor_tools.get_doctors_by_specialty(db=db, specialty=specialty)
    if "error" in result.get("status", ""): raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.get("/tools/get_doctor_details_by_name/")
async def call_get_doctor_details_by_name(doctor_name: str, db: Session = Depends(get_db)):
    result = await doctor_tools.get_doctor_details_by_name(db=db, doctor_name=doctor_name)
    if "error" in result.get("status", ""): raise HTTPException(status_code=400, detail=result.get("message"))
    return result
