
import json, os
from pathlib import Path
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
API_URL = os.getenv("VERIDIAN_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Veridian IT Service Agent", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
.main { background: #f7f8fb; }
.block-container { padding-top: 1.2rem; }
.hero { padding: 1.3rem 1.5rem; border-radius: 14px; background: linear-gradient(135deg,#172554,#334155); color:white; margin-bottom:1rem; }
.hero h1 { margin:0; font-size:2rem; }
.hero p { margin:.35rem 0 0; opacity:.9; }
.card { padding: 1rem; border:1px solid #e5e7eb; border-radius:12px; background:white; }
.small { color:#64748b; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def get_json(path):
    r = requests.get(API_URL + path, timeout=5)
    r.raise_for_status()
    return r.json()

def post_agent(message, employee, email):
    r = requests.post(API_URL + "/api/agent", json={"message":message,"employee":employee,"email":email}, timeout=15)
    r.raise_for_status()
    return r.json()

# Sidebar
with st.sidebar:
    st.header("Agent Controls")
    employee = st.text_input("Employee name", "Demo User")
    email = st.text_input("Employee email", "demo@veridian-corp.example")
    st.divider()
    st.subheader("Try a test case")
    tests = [
        "Can I get Wi-Fi access for a guest visiting tomorrow?",
        "I'm locked out of my account, tried my password 6 times.",
        "I think I got a phishing email asking for my login.",
        "My laptop screen is flickering and I've had it 2 years.",
        "New contractor joining next week needs VPN access.",
        "hey can you help, its not working"
    ]
    for i,t in enumerate(tests):
        if st.button(t, key=f"test{i}", use_container_width=True):
            st.session_state["prompt"] = t
            st.session_state["active_tab"] = 0
            st.rerun()
    st.divider()
    try:
        health = requests.get(API_URL + "/health", timeout=2).json()
        st.success("Backend connected")
    except Exception:
        st.error("Backend not running")
        st.caption("Run: python run.py")

st.markdown('<div class="hero"><h1>🛠️ Veridian IT Service Agent</h1><p>Policy-grounded internal IT support • AIONOS Assignment 2</p></div>', unsafe_allow_html=True)

tabs = st.tabs(["💬 Agent", "📋 Employee Requests", "🎫 Ticket Queue", "📚 Knowledge Base", "🧾 Audit"])

# AGENT
with tabs[0]:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.session_state.pop("prompt", None)
    typed = st.chat_input("Describe your IT issue...")
    if typed:
        prompt = typed

    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        try:
            result = post_agent(prompt, employee, email)
            source = result["source"]["id"] + " — " + result["source"]["title"] if result.get("source") else "No supplied policy"
            reply = result["response"] + f"\n\n**Source:** `{source}`"
            st.session_state.messages.append({"role":"assistant","content":reply})
            st.session_state["last_result"] = result
            st.rerun()
        except Exception as e:
            st.error(f"Backend error: {e}")

    if st.session_state.get("last_result"):
        r = st.session_state["last_result"]
        st.divider()
        st.subheader("Decision")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Intent", r["intent"].replace("_"," ").title())
        c2.metric("Confidence", f"{int(r['confidence']*100)}%")
        c3.metric("Action", r["action"])
        c4.metric("Priority", r["priority"])

        st.subheader("Structured Ticket")
        st.json({
            "ticket_id": r["ticket_id"],
            "category": r["intent"],
            "department": r["department"],
            "status": r["status"],
            "priority": r["priority"],
            "source": r["source"]["id"] if r.get("source") else "No supplied policy"
        })

        st.subheader("Audit Trail")
        for item in r["audit"]:
            st.write(f"**{item['time']}** — {item['event']}" + (f" — {item['detail']}" if item.get("detail") else ""))

        st.subheader("Policy Source")
        if r.get("source"):
            st.info(f"**{r['source']['id']} — {r['source']['title']}**\n\n{r['source']['text']}")
        else:
            st.warning("No directly applicable supplied policy was found. The agent did not invent one.")

# REQUESTS
with tabs[1]:
    st.subheader("Provided Employee Requests")
    data = get_json("/api/requests")
    st.dataframe(data, use_container_width=True, hide_index=True)
    st.caption("These are the 15 employee requests supplied in the assignment data pack.")

# TICKETS
with tabs[2]:
    st.subheader("Ticket Queue")
    data = get_json("/api/tickets")
    st.markdown("**Supplied queue**")
    st.dataframe(data["supplied"], use_container_width=True, hide_index=True)
    st.markdown("**Tickets created during this demo**")
    if data["created"]:
        st.dataframe(data["created"], use_container_width=True, hide_index=True)
    else:
        st.info("No demo tickets created yet.")

# KB
with tabs[3]:
    st.subheader("Knowledge Base")
    for p in get_json("/api/policies"):
        with st.expander(f"{p['id']} — {p['title']}"):
            st.write(p["text"])
            st.caption(f"Department: {p['department']} • Category: {p['category']}")

# AUDIT
with tabs[4]:
    st.subheader("Audit Log")
    data = get_json("/api/audit")
    if data:
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("Audit events will appear after you run a request.")

st.divider()
st.caption("Prototype: decisions are grounded only in the supplied assignment data. No real account unlock, access grant, security report, or hardware fulfillment is performed.")
