from fastapi import FastAPI, Request, BackgroundTasks
from app.devin import trigger_devin_remediation, wait_for_devin_completion
from app.tracker import log_session, init_db, update_session
import uuid

app = FastAPI(title="Devin Sentinel Automation")

@app.on_event("startup")
def startup_event():
    init_db()

# Make sure to import your new functions at the top:
# from app.devin import trigger_devin_remediation, wait_for_devin_completion
# from app.tracker import log_session, update_session, init_db

def process_ci_failure(repo_url: str, failure_details: str):
    run_id = str(uuid.uuid4())[:8] 
    issue_title = f"[DEVIN-AUTO] Fix CI Security Scan Failure ({run_id})"
    
    print(f"Automated CI Failure detected. Triggering Devin run: {run_id}...")
    
    try:
        # 1. Start the Session
        session_id = trigger_devin_remediation(repo_url, issue_title, failure_details)
        
        log_session(
            run_id=run_id, 
            session_id=session_id, 
            status="IN_PROGRESS",
            repository=repo_url
        )
        print(f"Devin Session Started: {session_id}. Waiting for completion...")
        
        # 2. Wait for Devin to finish and get the summary
        final_status, action_summary = wait_for_devin_completion(session_id)
        
        # 3. Update the database with the concise details
        update_session(
            run_id=run_id,
            status=final_status,
            devin_summary=action_summary # <--- Here is your concise detail!
        )
        print(f"Run {run_id} finished with status: {final_status}")
        
    except Exception as e:
        print(f"Failed to start/monitor Devin: {e}")
        update_session(run_id=run_id, status="FAILED", error_message=str(e))

        
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
