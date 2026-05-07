from fastapi import FastAPI, Request, BackgroundTasks
from app.devin import trigger_devin_remediation
from app.tracker import log_session, init_db
import uuid

app = FastAPI(title="Devin Sentinel Automation")

@app.on_event("startup")
def startup_event():
    init_db()

def process_ci_failure(repo_url: str, failure_details: str):
    """Background task to handle Devin without blocking the CI pipeline."""

    run_id = str(uuid.uuid4())[:8] 
    issue_title = f"[DEVIN-AUTO] Fix CI Security Scan Failure ({run_id})"
    
    print(f"Automated CI Failure detected. Triggering Devin run: {run_id}...")
    
    try:
        session_id = trigger_devin_remediation(repo_url, issue_title, failure_details)
        log_session(run_id, session_id, "INITIALIZED")
        print(f"Devin Session Started: {session_id}")
    except Exception as e:
        print(f"Failed to start Devin: {e}")
        try:
            log_session(run_id, "N/A", f"FAILED: {str(e)}")
        except Exception as log_err:
            print(f"Failed to log session: {log_err}")

@app.post("/webhook")
async def ci_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receives custom webhook payloads from our GitHub Action."""
    payload = await request.json()
    
    if payload.get("event_type") == "automated_scan_failure":
        repo_url = payload.get("repository", {}).get("html_url")
        details = payload.get("details", "No details provided.")
        
        background_tasks.add_task(process_ci_failure, repo_url, details)
        return {"status": "accepted", "message": "Devin remediation triggered by CI failure."}
            
    return {"status": "ignored", "message": "Event not applicable."}

@app.get("/status")
def get_status():
    """Endpoint for Observability / VP of Eng to check system state."""
    import json
    with open("data/runs.json", "r") as f:
        runs = json.load(f)
    return {"total_runs": len(runs), "history": runs}
