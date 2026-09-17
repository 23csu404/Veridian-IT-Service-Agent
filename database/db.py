
import sqlite3, json, uuid
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "veridian.db"
DATA = ROOT / "data"

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        employee TEXT NOT NULL,
        email TEXT NOT NULL,
        category TEXT,
        issue TEXT NOT NULL,
        action TEXT,
        priority TEXT,
        department TEXT,
        status TEXT,
        source TEXT,
        created_at TEXT,
        audit_json TEXT
    );
    CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT,
        event_time TEXT,
        event TEXT,
        detail TEXT
    );
    """)
    c.commit()
    c.close()

def create_ticket(employee, email, issue, result):
    ticket_id = "IT-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4].upper()
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = result["source"]["id"] if result.get("source") else "No supplied policy"
    c = conn()
    c.execute("""INSERT INTO tickets
      (ticket_id,employee,email,category,issue,action,priority,department,status,source,created_at,audit_json)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
      (ticket_id, employee, email, result["intent"], issue, result["action"], result["priority"],
       result["department"], result["status"], source, created, json.dumps(result["audit"])))
    for e in result["audit"]:
        c.execute("INSERT INTO audit(ticket_id,event_time,event,detail) VALUES(?,?,?,?)",
                  (ticket_id, e["time"], e["event"], e.get("detail","")))
    c.commit()
    c.close()
    return ticket_id

def list_created_tickets():
    c = conn()
    rows = [dict(x) for x in c.execute("SELECT * FROM tickets ORDER BY created_at DESC").fetchall()]
    c.close()
    return rows

def list_audit(ticket_id=None):
    c = conn()
    if ticket_id:
        rows = [dict(x) for x in c.execute("SELECT * FROM audit WHERE ticket_id=? ORDER BY id", (ticket_id,)).fetchall()]
    else:
        rows = [dict(x) for x in c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200").fetchall()]
    c.close()
    return rows
