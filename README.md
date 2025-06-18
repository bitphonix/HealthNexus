# 🩺 Doctor Appointment Assistant (Agentic AI with MCP)

This is a full-stack web application designed to streamline doctor appointment scheduling, confirmations, and internal reporting using an intelligent Agentic AI. The backend leverages FastAPI to expose powerful tools via a Microservice Coordination Pattern (MCP), which are then consumed by a LangChain-powered agent.

## ✨ Features

* **Intelligent Agent:** A LangChain agent (powered by OpenAI GPT-4o or Google Gemini Pro) handles natural language requests for appointment management.
* **Role-Based Interaction:** The agent can operate in "patient" mode (for booking/inquiring about appointments) or "doctor" mode (for retrieving reports and summaries).
* **Microservice Coordination Pattern (MCP):** Backend functionalities (DB operations, external API calls) are exposed as granular, self-contained tools via a dedicated FastAPI server (`mcp_server.py`).
* **Database Integration:** Manages doctor, patient, doctor availability, and appointment data using PostgreSQL and SQLAlchemy.
* **Google Calendar Integration:** Creates calendar events for booked appointments, ensuring doctors' schedules are updated.
* **Email Confirmation:** Sends automated email confirmations to patients upon successful appointment booking.
* **Slack Notifications:** Notifies doctors (via Slack webhooks) with daily appointment summaries or specific reports.
* **Minimalist Frontend:** A simple HTML/CSS/JS interface provides a chat-like experience for users to interact with the agent.

## 📦 Project Structure