# Architecture

```text
Employee
   ↓
Streamlit Frontend
   ↓ HTTP/JSON
FastAPI Backend
   ↓
Agent Orchestrator
   ├── Intent Detection
   ├── Entity Extraction
   ├── TF-IDF Policy Retrieval
   └── Controlled Decision Engine
          ├── Resolve
          ├── Clarify
          └── Escalate
   ↓
SQLite Ticket Store
   ↓
Audit Log + Source Policy
```

The language/retrieval layer is separated from the policy decision layer. This prevents the prototype from inventing unsupported approval workflows.
