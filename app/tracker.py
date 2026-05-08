import json
import os
from datetime import datetime

DATA_FILE = "data/runs.json"

def init_db():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    else:
        try:
            with open(DATA_FILE, "r") as f:
                json.load(f)
        except (json.JSONDecodeError, ValueError):
            with open(DATA_FILE, "w") as f:
                json.dump([], f)

def log_session(run_id, session_id, status, **kwargs):
    init_db()
    with open(DATA_FILE, "r") as f:
        runs = json.load(f)
    
    # Create the base entry
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": run_id,
        "devin_session_id": session_id,
        "status": status,
    }
    
    # If any extra metadata was passed, attach it under a 'metadata' key
    if kwargs:
        entry["metadata"] = kwargs
    
    runs.append(entry)
    
    with open(DATA_FILE, "w") as f:
        json.dump(runs, f, indent=4)
    
def update_session(run_id, status, **kwargs):
    """Finds an existing run and updates its status and metadata."""
    init_db()
    with open(DATA_FILE, "r") as f:
        runs = json.load(f)
    
    for run in runs:
        if run.get("run_id") == run_id:
            run["status"] = status
            run["timestamp_completed"] = datetime.utcnow().isoformat()
            
            # Merge new metadata (like the Devin summary) with the existing metadata
            if "metadata" not in run:
                run["metadata"] = {}
            run["metadata"].update(kwargs)
            break
            
    with open(DATA_FILE, "w") as f:
        json.dump(runs, f, indent=4)

