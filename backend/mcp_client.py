# backend/mcp_client.py

import asyncio
from langchain.tools import StructuredTool
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel, Field
from backend.database import get_db_context  # <-- Import the new context manager
from backend.mcp_tools import appointment_tools, availability_tools, doctor_tools, reporting_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookAppointmentInput(BaseModel):
    patient_email: str = Field(description="The email address of the patient.")
    doctor_email: str = Field(description="The email address of the doctor.")
    appointment_time_str: str = Field(description="The desired appointment time in 'YYYY-MM-DD HH:MM:SS' format.")
    reason: Optional[str] = Field(None, description="The reason for the appointment.")

class CheckAvailabilityInput(BaseModel):
    doctor_name_or_email: str = Field(description="The name or email of the doctor to check.")
    target_date_str: Optional[str] = Field(None, description="The target date in 'YYYY-MM-DD' format. Defaults to today.")

class GetSummaryInput(BaseModel):
    doctor_email: str = Field(description="The email address of the doctor for whom to get the summary.")
    target_date_str: Optional[str] = Field(None, description="The target date in 'YYYY-MM-DD' format. Defaults to today.")

class GetDoctorsInput(BaseModel):
    specialty: str = Field(description="The medical specialty to search for, e.g., 'General Practice', 'Neurology'.")

class GetDoctorDetailsInput(BaseModel):
    doctor_name: str = Field(description="The full name of the doctor to look up details for.")


class MCPClient:
    def _create_async_tool_func(self, tool_async_func):
        async def wrapper(**kwargs):
            with get_db_context() as db:
                return await tool_async_func(db=db, **kwargs)
        return wrapper

    def _create_sync_tool_func(self, tool_async_func):
        async_func = self._create_async_tool_func(tool_async_func)
        def wrapper(**kwargs):
            return asyncio.run(async_func(**kwargs))
        return wrapper

    def get_langchain_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                name="book_appointment",
                description="Use this to book a new appointment.",
                func=self._create_sync_tool_func(appointment_tools.book_appointment),
                coro=self._create_async_tool_func(appointment_tools.book_appointment),
                args_schema=BookAppointmentInput
            ),
            StructuredTool.from_function(
                name="check_doctor_availability",
                description="Check when a doctor is available.",
                func=self._create_sync_tool_func(availability_tools.check_doctor_availability),
                coro=self._create_async_tool_func(availability_tools.check_doctor_availability),
                args_schema=CheckAvailabilityInput
            ),
            StructuredTool.from_function(
                name="get_appointments_summary_for_doctor",
                description="Get a summary of a doctor's appointments.",
                func=self._create_sync_tool_func(reporting_tools.get_appointments_summary_for_doctor),
                coro=self._create_async_tool_func(reporting_tools.get_appointments_summary_for_doctor),
                args_schema=GetSummaryInput
            ),
            StructuredTool.from_function(
                name="get_doctors_by_specialty",
                description="Find doctors by their specialty.",
                func=self._create_sync_tool_func(doctor_tools.get_doctors_by_specialty),
                coro=self._create_async_tool_func(doctor_tools.get_doctors_by_specialty),
                args_schema=GetDoctorsInput
            ),
            StructuredTool.from_function(
                name="get_doctor_details_by_name",
                description="Get details for a specific doctor.",
                func=self._create_sync_tool_func(doctor_tools.get_doctor_details_by_name),
                coro=self._create_async_tool_func(doctor_tools.get_doctor_details_by_name),
                args_schema=GetDoctorDetailsInput
            ),
        ]