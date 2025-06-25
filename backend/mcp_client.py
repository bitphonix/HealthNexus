# backend/mcp_client.py
import httpx
from langchain.tools import StructuredTool
from typing import Dict, Any, List, Optional, Awaitable
import logging
from pydantic import BaseModel, Field
import asyncio
import functools

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
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def _sync_wrapper(self, coro: Awaitable, **kwargs) -> Any:
        return asyncio.run(coro(**kwargs))

    async def _call_tool(self, tool_name: str, method: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        timeout = httpx.Timeout(30.0, connect=5.0)
        async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout) as client:
            try:
                endpoint = f"/tools/{tool_name}/"
                if method.upper() == "POST": response = await client.post(endpoint, json=json_data)
                else: response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e: return {"status": "error", "message": f"Tool failed: {e.response.text}"}
            except Exception as e: return {"status": "error", "message": f"Client error: {e}"}

    async def book_appointment(self, **kwargs) -> Dict[str, Any]:
        return await self._call_tool("book_appointment", "POST", json_data=kwargs)

    async def check_doctor_availability(self, **kwargs) -> Dict[str, Any]:
        return await self._call_tool("check_doctor_availability", "GET", params=kwargs)

    async def get_appointments_summary_for_doctor(self, **kwargs) -> Dict[str, Any]:
        return await self._call_tool("get_appointments_summary_for_doctor", "GET", params=kwargs)
    
    async def get_doctors_by_specialty(self, **kwargs) -> Dict[str, Any]:
        return await self._call_tool("get_doctors_by_specialty", "GET", params=kwargs)

    async def get_doctor_details_by_name(self, **kwargs) -> Dict[str, Any]:
        return await self._call_tool("get_doctor_details_by_name", "GET", params=kwargs)
    
    async def close(self): pass

    def get_langchain_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(name="book_appointment", description="Use this tool to book a new appointment.", func=functools.partial(self._sync_wrapper, self.book_appointment), coro=self.book_appointment, args_schema=BookAppointmentInput),
            StructuredTool.from_function(name="check_doctor_availability", description="Use this tool to check when a doctor is available.", func=functools.partial(self._sync_wrapper, self.check_doctor_availability), coro=self.check_doctor_availability, args_schema=CheckAvailabilityInput),
            StructuredTool.from_function(name="get_appointments_summary_for_doctor", description="Use this tool to get a summary of a doctor's appointments.", func=functools.partial(self._sync_wrapper, self.get_appointments_summary_for_doctor), coro=self.get_appointments_summary_for_doctor, args_schema=GetSummaryInput),
            StructuredTool.from_function(name="get_doctors_by_specialty", description="Use this tool to find doctors by their specialty.", func=functools.partial(self._sync_wrapper, self.get_doctors_by_specialty), coro=self.get_doctors_by_specialty, args_schema=GetDoctorsInput),
            StructuredTool.from_function(name="get_doctor_details_by_name", description="Use this tool to get details about a specific doctor, like their specialty.", func=functools.partial(self._sync_wrapper, self.get_doctor_details_by_name), coro=self.get_doctor_details_by_name, args_schema=GetDoctorDetailsInput),
        ]