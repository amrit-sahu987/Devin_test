import json
import os
from datetime import datetime

DATA_FILE = "data/runs.json"

def init_db():
    if not os.path.exists(DATA_FILE):
        os.makedirs("data", exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def log_session(issue_id, session_id, status):
    init_db()
    with open(DATA_FILE, "r") as f:
        runs = json.load(f)
    
    runs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "issue_id": issue_id,
        "devin_session_id": session_id,
        "status": status
    })
    
    with open(DATA_FILE, "w") as f:
        json.dump(runs, f, indent=4)