# Doctor Appointment Assistant

## 🚀 Project Overview

This is a full-stack web application featuring an advanced, agentic AI powered by LangChain and Google's Gemini model. The agent serves as a "Doctor Appointment Assistant," capable of dynamically using a suite of tools to handle user requests for booking, checking availability, and reporting. The backend is built with FastAPI, and it interacts with a PostgreSQL database, Google Calendar, Gmail for email confirmations, and Slack for notifications.

### Core Features

*   **Conversational Appointment Booking:** Patients can book appointments in a natural, conversational manner.
*   **Real-Time Availability Checking:** The agent uses tools to check the database and the doctor's Google Calendar to find open slots.
*   **Automated Confirmations:** Successfully booked appointments trigger a confirmation email to the patient and create a Google Calendar event.
*   **Doctor Reporting Tools:** Doctors can query the system for appointment summaries, which are also sent as notifications to a Slack channel.
*   **Stateful Conversations:** The agent uses memory to remember the user's name, email, and other details throughout the booking process.

## 🔧 Tech Stack

*   **Backend:** FastAPI, Python, SQLAlchemy
*   **Database:** PostgreSQL
*   **AI/Agent:** LangChain, Google Gemini
*   **Services:** Google Calendar API, Gmail SMTP API, Slack Webhooks
*   **Frontend:** HTML, CSS, JavaScript

---

## 🛠️ Setup & Run Instructions

Follow these steps to set up and run the project locally.

### Prerequisites

*   Python 3.9+
*   Git
*   PostgreSQL installed and running.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/doctor-appointment-agent.git
cd doctor-appointment-agent```

### 2. Set Up Virtual Environment

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL

1.  Make sure your PostgreSQL server is running.
2.  Create a new database for this project (e.g., `doctor_appointments`).
3.  You will need the database connection URL (e.g., `postgresql://user:password@localhost/doctor_appointments`).

### 5. Configure Environment Variables

1.  In the project's root directory, create a file named `.env`.
2.  Copy the contents of `.env.example` into your new `.env` file.
3.  Fill in the values for each variable:
    *   `DATABASE_URL`: Your PostgreSQL connection URL from the previous step.
    *   `GOOGLE_API_KEY`: Your API key for the Gemini model from Google AI Studio.
    *   `GMAIL_SENDER`: The Gmail address the confirmation emails will be sent from.
    *   `GMAIL_APP_PASSWORD`: The 16-character App Password for the `GMAIL_SENDER` account.
    *   `SLACK_WEBHOOK_URL`: Your Slack Incoming Webhook URL.

### 6. Google API Setup (Calendar)

This project uses the Google Calendar API.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Google Calendar API**.
4.  Go to **Credentials** -> **Create Credentials** -> **OAuth client ID**.
5.  Select **Desktop app** as the application type and give it a name.
6.  Click **Download JSON**. Rename the downloaded file to `google_creds_v2.json` and place it in the project's root directory.
7.  Go to the **OAuth Consent Screen**, click `EDIT APP`, and set the **App name** (e.g., "Doctor Appointment Assistant"). Fill in the required email fields and save.

### 7. Run the Application

1.  **Run the FastAPI Server:**
    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```
2.  **Open in Browser:** Navigate to `http://127.0.0.1:8000`.
3.  **(First Run Only) Authenticate Google Calendar:** The first time a calendar tool is used, a browser window will open asking you to log in and grant permission. This will create a `token.json` file in your project.
4.  **Seed the Database:** Click the "Seed Database" button on the web page to populate the database with sample doctors and availability.

---

## 🧰 Tool Summary

The agent has access to the following tools exposed via the FastAPI backend:

| Tool Name                             | Description                                            |
| ------------------------------------- | ------------------------------------------------------ |
| `get_doctors_by_specialty`            | Finds doctors based on a medical specialty.            |
| `check_doctor_availability`           | Checks a doctor's schedule for open slots on a date.   |
| `book_appointment`                    | Books an appointment, sends email, and creates event.  |
| `get_appointments_summary_for_doctor` | Gets a summary of a doctor's appointments for a date.  |
| `get_doctor_details_by_name`          | Retrieves details for a specific doctor.               |

## 🗣️ Sample Prompts

### Patient Role

*   "hello my name is Tanishk Soni, I am having Migraine i want to see a Neurologist."
*   "Are there any openings with Dr. Evelyn Reed tomorrow?"

### Doctor Role

*   "Can you give me a summary of my appointments for 2025-06-19? My email is e.reed.neuro@clinic.com."
*   "How many patients do we have scheduled for today?"