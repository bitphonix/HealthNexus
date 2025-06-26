import os
import logging
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from backend.mcp_client import MCPClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DoctorAppointmentAgent:
    def __init__(self, role: str = "patient"):
        self.mcp_client = MCPClient()
        self.tools = self.mcp_client.get_langchain_tools()
        self.role = role

        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in .env file. Please set it to run the agent.")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0,
            convert_system_message_to_human=True
        )

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        self.agent_executor = self._create_agent_executor()
        logger.info(f"Agent initialized for role: {self.role} with model gemini-1.5-flash-latest")

    def _create_agent_executor(self) -> AgentExecutor:
        if self.role == "patient":
            system_prompt = (
                "You are a tool-using AI. Your only goal is to book doctor appointments by following these rules precisely. You MUST use your tools. Do not make up information.\n\n"
                "*CRITICAL BEHAVIOR:*\n"
                "1.  *Memory Rule:* You have a short-term memory. You MUST remember key information throughout the conversation: the patient_email, doctor_email from tools, and the reason for the appointment.\n"
                "2.  *Execution Rule:* When you use the final book_appointment tool, you MUST use the exact values you remembered.\n\n"
                
                "*WORKFLOW:*\n"
                "1.  *Get Patient Email:* Ask the user for their email and wait for their response.\n"
                "2.  *Get Specialty:* Ask the user for the medical specialty they need.\n"
                "3.  *Find Doctor & REMEMBER Email:* Use the get_doctors_by_specialty tool. When it returns a doctor, you MUST find their email in the tool's output. Your next thought must be to explicitly state: 'I will remember this exact email for the final booking.'\n"
                "4.  *Get Reason:* Ask the user for the reason/symptoms for their appointment (e.g., 'What's the reason for your visit?' or 'What symptoms are you experiencing?').\n"
                "5.  *Check Availability:* Ask for a date and use the check_doctor_availability tool with the doctor's information.\n"
                "6.  *Get Time Choice:* Present the list of available time strings from the tool's output and get the user's choice.\n"
                "7.  *Confirm and Book:* Ask for final confirmation. Then, use the book_appointment tool with the exact patient_email, doctor_email, appointment time, and reason you collected."
            )
        else: 
            system_prompt = (
                "PRIMARY DIRECTIVE: You are an informational AI assistant for doctors. Your only purpose is to use the provided tools to answer questions about appointments and patients. You have full permission to use all tools.\n\n"
                
                "RULES:\n"
                "1.  You MUST use your tools to answer questions. Do not claim you cannot access information if a tool is available for it.\n"
                "2.  If the user says 'today', you MUST understand that you should use the current date for the `target_date_str` parameter if the tool requires it. Do not ask the user for the date if they say 'today'.\n\n"
                
                "AVAILABLE TOOLS:\n"
                "- `get_appointments_summary_for_doctor`: Use this to get a list of appointments for a specific doctor on a specific date.\n"
                "- `get_patient_count_by_date`: Use this to count patients on a given date.\n"
                "- `get_patients_with_condition`: Use this to find patients with a specific condition."
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )

    async def run(self, prompt: str) -> Dict[str, Any]:
        """Runs the agent with the given prompt and returns the response."""
        logger.info(f"Agent running prompt (role: {self.role}): {prompt}")
        try:
            response = await self.agent_executor.ainvoke({"input": prompt})
            return {"response": response.get("output", "I'm sorry, I couldn't process that.")}
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            return {"response": f"I'm sorry, but an unexpected error occurred. Please try again later."}

    async def close(self):
        """A method to clean up resources if needed in the future."""
        await self.mcp_client.close()