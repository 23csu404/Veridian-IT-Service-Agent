
from agent.core import run_agent

def test_guest_wifi():
    r = run_agent("Can I get Wi-Fi access for a guest tomorrow?")
    assert r["intent"] == "guest_wifi"
    assert r["action"] == "RESOLVE"
    assert r["source"]["id"] == "KB-07"

def test_password_lockout():
    r = run_agent("I tried my password 6 times and am locked out")
    assert r["intent"] == "password_lockout"
    assert r["action"] == "ESCALATE"
    assert r["source"]["id"] == "KB-01"

def test_phishing():
    r = run_agent("I received a phishing email asking for my login")
    assert r["intent"] == "security_incident"
    assert r["action"] == "ESCALATE"
    assert r["source"]["id"] == "KB-09"

def test_ambiguous():
    r = run_agent("hey can you help, its not working")
    assert r["intent"] == "unknown"
    assert r["action"] == "CLARIFY"
