
from pathlib import Path
import json
from fastapi import FastAPI
from pydantic import BaseModel
from agent.core import run_agent
from database.db import init_db, create_ticket, list_created_tickets, list_audit

ROOT = Path(__file__).resolve().parent.parent
init_db()

app = FastAPI(title="Veridian IT Service Agent API", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    employee: str = "Demo User"
    email: str = "demo@veridian-corp.example"

@app.get("/health")
def health():
    return {"status":"ok","service":"Veridian IT Service Agent"}

@app.post("/api/agent")
def agent(req: ChatRequest):
    result = run_agent(req.message)
    ticket_id = create_ticket(req.employee, req.email, req.message, result)
    result["ticket_id"] = ticket_id
    result["audit"].append({"time": result["audit"][-1]["time"], "event": f"Ticket created: {ticket_id}"})
    return result

@app.get("/api/policies")
def policies():
    return json.loads((ROOT/"data/policies.json").read_text(encoding="utf-8"))

@app.get("/api/requests")
def requests():
    return json.loads((ROOT/"data/employee_requests.json").read_text(encoding="utf-8"))

@app.get("/api/tickets")
def tickets():
    supplied = json.loads((ROOT/"data/tickets.json").read_text(encoding="utf-8"))
    return {"supplied": supplied, "created": list_created_tickets()}

@app.get("/api/audit")
def audit(ticket_id: str | None = None):
    return list_audit(ticket_id)
