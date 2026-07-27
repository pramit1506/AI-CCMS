# AIVOA Customer Complaint Management System

This project is an AI-first CCMS module for logging customer complaints through a conversational assistant.

The application has a React frontend with a live complaint details panel and a FastAPI backend powered by LangGraph and Groq. The assistant extracts structured CCMS fields from natural language, asks clarification questions when information is missing, updates the draft in real time, and executes workflow tools once the complaint is ready.

## Features

- Conversational customer complaint logging
- Live complaint draft updates in the frontend
- Multi-turn clarification flow for missing required fields
- Safe multi-complaint handling
- Editing of the active logged complaint
- Follow-up date and action generation
- Complaint summarization
- Compliance checking for completed complaints
- Backend test coverage for graph, tools, services, APIs, and workflows

## Tech Stack

- Frontend: React, Vite, TypeScript, Redux Toolkit
- Backend: FastAPI, Pydantic v2, SQLAlchemy async, Alembic
- Agent workflow: LangGraph
- LLM provider: Groq
- Database: PostgreSQL
- Testing: Pytest, Vitest

## LangGraph Tools

The backend registers five LangGraph tools:

- `log_interaction`: creates a new customer complaint record
- `edit_interaction`: updates the active complaint record
- `generate_followup`: generates follow-up actions from complaint context
- `summarize_interaction`: creates a concise complaint summary
- `compliance_check`: checks complaint content for compliance issues

## Project Structure

```text
AI CCMS/
  backend/
    app/
      api/              FastAPI routes
      core/             application settings and logging
      database/         database base/session setup
      graph/            LangGraph state, nodes, router, builder
      llm/              LLM provider abstraction and Groq provider
      models/           SQLAlchemy models
      repositories/     data access layer
      schemas/          Pydantic request/response/domain schemas
      services/         business logic and workflow services
      tools/            LangGraph tool implementations
      utils/            response and draft helpers
    tests/              backend unit and integration tests
    alembic/            database migration setup

  frontend/
    src/
      components/       React UI components
      redux/            Redux Toolkit slices and store
      services/         API client and response mapping
      types/            TypeScript types
    tests/              frontend tests
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL
- Groq API key

## Environment Setup

Create a backend environment file:

```powershell
cd backend
copy .env.example .env
```

Update `backend/.env` with your local values:

```env
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_hcp_crm"
GROQ_API_KEY="your-groq-api-key"
DEFAULT_MODEL="llama-3.3-70b-versatile"
```

Make sure the PostgreSQL database exists before starting the backend.

## Run The Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If you already activated the virtual environment:

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend runs at:

```text
http://127.0.0.1:8000
```

## Run The Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open the app in the browser:

```text
http://127.0.0.1:5173
```

If PowerShell blocks `npm`, use:

```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

## Verification

Run backend tests:

```powershell
cd backend
$env:PYTHONPATH="E:\AI Customer\backend"
pytest
```

Run frontend tests:

```powershell
cd frontend
npm.cmd test -- --run
```

Build the frontend:

```powershell
cd frontend
npm.cmd run build
```

Current verification status:

- Backend: 71 tests passing
- Frontend: 8 tests passing
- Frontend production build passing

## Suggested Demo Flow

1. Start the backend and frontend.
2. Open the frontend at `http://127.0.0.1:5173`.
3. Ask the assistant to log an complaint, for example:

```text
Log an complaint with Customer.
```

4. Answer clarification questions naturally:

```text
Today at 1 PM.
It was a phone call.
We discussed reports and suggested medications. It is completed.
```

5. Show the left-side complaint draft updating live.
6. Let `log_interaction` execute and show the CCMS success state.
7. Edit the active complaint:

```text
Add a follow-up in 15 days.
```

8. Demonstrate the remaining tools:

```text
Generate a follow-up for this complaint.
Summarize this complaint.
Run a compliance check.
```

9. To start a second complaint, use explicit wording:

```text
Log another complaint with Customer.
```

The app intentionally keeps the current complaint active unless the user clearly asks to log another/new complaint or answers yes when prompted.

## Notes

- Required fields for logging an complaint include customer information, date, complaint type, status, and discussion summary.
- The assistant asks clarification questions instead of creating incomplete records.
- After an complaint is logged, edits and follow-ups stay attached to the active complaint unless the user explicitly starts a new one.
