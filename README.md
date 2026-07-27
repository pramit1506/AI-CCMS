
# AI-Powered Customer Complaint Management System

**AIVOA Round 1 AI Product Engineer Assignment**

## Assignment Overview

This project is an AI-powered Customer Complaint Management System (CCMS) built for the pharmaceutical manufacturing industry. It fulfills the AIVOA Round 1 Assignment by providing a conversational AI Complaint Intake Assistant that extracts structured QMS (Quality Management System) data from natural language and auto-populates a Complaint Draft in real time.

## Project Features

- **Paste complaint text**: Users can provide complaint details via natural language chat input.
- **AI-powered complaint extraction**: Automatically extracts critical entities (Origin, Customer Details, Product & Batch ID, Complaint Details).
- **Auto-populate complaint form**: Live updates to the Complaint Draft on the frontend React UI.
- **Complaint editing through AI chat**: Users can refine, correct, or remove details conversationally.
- **Complaint Completeness Checker**: The AI assistant proactively asks for missing required information via a multi-turn clarification flow.
- **AI Risk Assessment**: Generates initial severity and priority based on complaint context.
- **Complaint Summary**: AI-generated concise summary of the reported complaint.
- **CAPA Recommendation / Root Cause Recommendation**: Intelligent action recommendations based on complaint details.
- **Save Complaint**: Persists the finalized Complaint Draft to the database.

## Technology Stack

**Frontend**
- React
- Redux Toolkit
- Vite
- TypeScript

**Backend**
- FastAPI
- LangGraph (AI Agent Framework)
- Groq LLM
- PostgreSQL
- SQLAlchemy
- Python

## Project Architecture

The architecture decouples the frontend and backend. The React frontend maintains the state using Redux Toolkit and communicates with the FastAPI backend. The backend uses LangGraph as the AI Agent Framework to orchestrate the AI Workflow, handling entity extraction, decision making, multi-turn memory, and tool execution securely.

## Folder Structure

```text
AI CCMS/
  backend/
    app/
      api/              FastAPI routes
      core/             Application settings and logging
      database/         Database base/session setup
      graph/            LangGraph state, nodes, router, builder
      llm/              LLM provider abstraction and Groq provider
      models/           SQLAlchemy models
      repositories/     Complaint Repository data access layer
      schemas/          Pydantic request/response/domain schemas
      services/         Complaint Services and business logic
      tools/            Complaint Tools implementations
      utils/            Response and draft helpers
    tests/              Backend unit and integration tests
    alembic/            Database migration setup

  frontend/
    src/
      components/       React UI components
      redux/            Redux Toolkit slices and store
      services/         API client and response mapping
      types/            TypeScript types
    tests/              Frontend tests
```

## Installation Steps

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL
- Groq API key

### Environment Variables

Create a backend environment file:

```powershell
cd backend
copy .env.example .env
```

Update `backend/.env` with your local values:

```env
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ccms_db"
GROQ_API_KEY="your-groq-api-key"
DEFAULT_MODEL="llama-3.3-70b-versatile"
```

Make sure the PostgreSQL database exists before starting the backend.

### Running Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend runs at: `http://127.0.0.1:8000`

### Running Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open the app in the browser: `http://127.0.0.1:5173`

## LangGraph Workflow

User Input
↓
Chat Input Endpoint
↓
Text Extraction
↓
LangGraph
↓
Entity Extraction
↓
Complaint Draft
↓
Risk Assessment
↓
Complaint Form Update
↓
Save Complaint

## AI Workflow

The AI Workflow leverages a Decision Engine node in LangGraph. When a user sends a message, the LLM first extracts structured QMS entities. The Decision Engine then evaluates if the Complaint Draft is complete. If information is missing (Complaint Completeness Checker), it triggers a clarification flow. Once complete, it executes relevant tools (like Save Complaint or Risk Assessment) and translates the final state into a conversational response.

## Complaint Upload Flow

Currently, complaints can be pasted into the chat interface as text. The LangGraph workflow intercepts this text, processes it through the entity extraction prompt, and auto-populates the Complaint Draft on the UI.

## Database Information

The system utilizes PostgreSQL for persistent storage. SQLAlchemy acts as the ORM, with asynchronous support via asyncpg. Alembic manages database migrations. The primary records stored are the validated Customer Complaints and their associated metadata.

## API Overview

The AI-First Conversation API provides a unified REST interface. Every chat interaction automatically returns both the conversational response from the AI Complaint Intake Assistant and the latest structured Complaint Draft state, allowing the React frontend to reflect backend AI reasoning in real time.

## Implemented AI Tools

- `save_complaint`: Commits a new customer complaint record to the Complaint Database.
- `edit_complaint`: Updates the active complaint record.
- `generate_capa`: Generates Root Cause and CAPA Recommendations.
- `summarize_complaint`: Creates a concise Complaint Summary.
- `completeness_check`: Checks complaint content for missing mandatory fields and compliance.

## Demo Instructions

1. Launch frontend
2. Launch backend
3. Paste complaint text into the AI Complaint Intake Assistant
4. AI extracts complaint details automatically
5. Complaint form populates live on the screen
6. Risk Assessment appears (Initial Severity, Priority)
7. User edits complaint via chat (e.g., "Add a CAPA recommendation")
8. Save Complaint triggers automatically or via explicit command
9. Reset Form to clear the current draft and start a new complaint session

## Known Limitations

- Multi-turn conversation memory is currently held in-memory and resets on server restart.
- Document parsing (PDF/OCR) is simulated via text paste capabilities as production-grade OCR was not required.
- The UI handles a single active complaint session at a time.

## Future Scope

- Integration with pharmaceutical ERP systems (e.g., SAP) for live Batch validation.
- Deployment of OCR services for native PDF/Email parsing.
- Persistent conversation memory backed by vector databases.

## Credits

Developed for the AIVOA AI Product Engineer Assignment.
```