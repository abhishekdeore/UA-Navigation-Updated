import subprocess
import webbrowser
import time
import os

print("Starting FastAPI backend...")
backend_process = subprocess.Popen(
    ["uvicorn", "fastapi_chatbot_backend:app", "--reload"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# === Step 2: Wait a few seconds for backend to spin up ===
time.sleep(3)

# === Step 3: Open homepage.html in default browser ===
html_path = os.path.abspath("homepage.html")
webbrowser.open(f"file://{html_path}")

print("🚀 UA Nav Access launched.")
