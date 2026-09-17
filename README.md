# Veridian IT Service Agent

A full-stack prototype for **AIONOS Agentic AI Factory — Assignment 2: Internal Service Agent**.

## Features

- Natural-language IT issue understanding
- Intent detection
- Entity extraction
- TF-IDF policy retrieval
- Policy-controlled decision engine
- Resolve / Clarify / Escalate outcomes
- Structured ticket creation
- SQLite persistence
- Audit trail
- Source policy display
- Supplied employee requests viewer
- Supplied ticket queue viewer
- Knowledge base viewer
- FastAPI backend + Streamlit frontend

## Run

### Windows / VS Code

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python run.py
```

Open the Streamlit URL shown in the terminal.

### Alternative

Terminal 1:
```bash
uvicorn backend.api:app --reload --port 8000
```

Terminal 2:
```bash
streamlit run frontend/app.py
```

## Project structure

```text
veridian-it-service-agent/
├── agent/
│   └── core.py
├── backend/
│   └── api.py
├── frontend/
│   └── app.py
├── database/
│   └── db.py
├── data/
│   ├── policies.json
│   ├── employee_requests.json
│   └── tickets.json
├── docs/
├── tests/
├── app.py
├── run.py
└── requirements.txt
```

## Design principle

The prototype does not use an unrestricted generative response as the final decision-maker. Natural-language input is mapped to an intent and relevant supplied policy, then a controlled decision layer determines whether to resolve, clarify, or escalate.

## Data constraint

Only the assignment's supplied policies and operational data are used. Unsupported policies or approval paths are not invented.

## Prototype limitation

The application simulates routing and ticket creation. It does not actually unlock accounts, grant access, send security emails, approve hardware, or perform real enterprise actions.

## AI/tool disclosure

In the final submission, list the tools actually used during development and what each contributed. Do not claim runtime integrations that are not implemented.
