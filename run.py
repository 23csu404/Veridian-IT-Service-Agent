import subprocess, sys, time

backend = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "backend.api:app",
    "--host", "127.0.0.1", "--port", "8000"
])
time.sleep(2)
frontend = subprocess.Popen([
    sys.executable, "-m", "streamlit", "run", "frontend/app.py",
    "--server.headless=true"
])
try:
    frontend.wait()
finally:
    backend.terminate()
    try:
        backend.wait(timeout=3)
    except Exception:
        backend.kill()
