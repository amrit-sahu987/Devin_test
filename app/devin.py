# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()
# DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
# DEVIN_API_URL = "https://api.devin.ai/v1/sessions" 

# def trigger_devin_remediation(repo_url, issue_title, issue_body):
#     """Initiates a Devin session with a highly specific prompt."""
    
#     prompt = f"""
#     You are an autonomous Security Engineer embedded in our CI/CD pipeline.
    
#     Context:
#     Our continuous integration pipeline just failed a security scan on this repository: {repo_url}
    
#     The security scanner output is as follows:
#     {issue_body} # (This variable now holds the failure details from the webhook)
    
#     Instructions:
#     1. Clone the repository and checkout a new branch named 'fix/ci-security-patch'.
#     2. Read the scanner output provided above to identify the vulnerable dependency.
#     3. Update the dependency in the requirements file to a secure version.
#     4. Run any basic formatting or linting tools available in the repo to ensure code quality.
#     5. Commit the changes and push the branch.
#     6. Open a Pull Request against the main branch. In the PR description, explicitly mention: "{issue_title}" and explain the fix.
    
#     Do not ask for user input. Execute this end-to-end and terminate the session when the PR is open.
#     """

#     headers = {
#         "Authorization": f"Bearer {DEVIN_API_KEY}",
#         "Content-Type": "application/json"
#     }
    
#     payload = {
#         "prompt": prompt
#     }

#     response = requests.post(DEVIN_API_URL, headers=headers, json=payload)
#     response.raise_for_status()
    
#     return response.json().get("session_id")

import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()
DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
# Ensure this URL is exactly as provided in your specific API dashboard
DEVIN_API_URL = "https://api.devin.ai/v1/sessions" 

def trigger_devin_remediation(repo_url, issue_title, issue_body):
    """Initiates a Devin session with a highly specific prompt."""
    
    prompt = f"""
    You are an autonomous Security Engineer embedded in our CI/CD pipeline.
    
    Context:
    Our continuous integration pipeline just failed a security scan on this repository: {repo_url}
    
    The security scanner output is as follows:
    {issue_body}
    
    Instructions:
    1. Clone the repository and checkout a new branch named 'fix/ci-security-patch'.
    2. Read the scanner output provided above to identify the vulnerable dependency.
    3. Update the dependency in the requirements file to a secure version.
    4. Run any basic formatting or linting tools available in the repo to ensure code quality.
    5. Commit the changes and push the branch.
    6. Open a Pull Request against the main branch. In the PR description, explicitly mention: "{issue_title}" and explain the fix.
    
    Do not ask for user input. Execute this end-to-end and terminate the session when the PR is open.
    """

    # We use both Authorization and x-api-key headers. 
    # Some Devin tiers prefer one over the other; providing both is a common fix for 403s.
    headers = {
        "Authorization": f"Bearer {DEVIN_API_KEY}",
        "x-api-key": DEVIN_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt
    }

    if not DEVIN_API_KEY:
        raise ValueError("DEVIN_API_KEY is not set. Please add it to your .env file.")

    print(f"Sending request to Devin API for: {issue_title}")
    
    response = requests.post(DEVIN_API_URL, headers=headers, json=payload)
    
    # Check for errors BEFORE raise_for_status to log the actual API message
    if response.status_code != 200:
        print("!!! DEVIN API ERROR !!!")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        # This will help you see if it's a 'Rate Limit', 'Invalid Key', or 'Org Restricted' error
    
    response.raise_for_status()
    
    # Return the session ID
    session_data = response.json()
    return session_data.get("session_id")

def wait_for_devin_completion(session_id, timeout_minutes=15):
    """Polls the API until Devin finishes, then extracts the summary."""
    headers = {
        "Authorization": f"Bearer {DEVIN_API_KEY}",
        "x-api-key": DEVIN_API_KEY,
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    
    # while (time.time() - start_time) < (timeout_minutes * 60):
    #     # Poll the session endpoint
    #     response = requests.get(f"{DEVIN_API_URL}/{session_id}", headers=headers)
    #     if response.status_code != 200:
    #         time.sleep(30)
    #         continue
            
    #     data = response.json()
    #     status = data.get("status_enum") or data.get("status")
        
    #     if status == "finished":
    #         # Extract the PR details! This is where the "concise summary" lives.
    #         pr_info = data.get("pull_request", {})
    #         pr_url = pr_info.get("url", "No PR URL provided")
    #         pr_title = pr_info.get("title", "No title provided")
            
    #         # Formulate the concise summary
    #         summary = f"Successfully created PR: {pr_title}. Link: {pr_url}"
    #         return "COMPLETED", summary
            
    #     elif status in ["expired", "failed", "blocked"]:
    #         return "FAILED", f"Devin stopped prematurely with status: {status}"
            
    #     # Wait 30 seconds before polling again to avoid rate limits
    #     print(f"Devin is still working on {session_id}... checking again in 30s.")
    #     time.sleep(30)
    while (time.time() - start_time) < (timeout_minutes * 60):
        response = requests.get(f"{DEVIN_API_URL}/{session_id}", headers=headers)
        
        if response.status_code != 200:
            print(f"API Error during poll: {response.status_code}")
            time.sleep(30)
            continue
            
        data = response.json()
        
        # Grab every possible status field to be safe
        status_enum = data.get("status_enum")
        status_str = data.get("status")
        state = data.get("state") # Sometimes it's hiding here
        
        # The true status is whichever one is actually populated
        current_status = status_enum or status_str or state
        
        print(f"[{int(time.time() - start_time)}s] Devin Status: '{current_status}'")
        
        # Expanded success conditions
        if current_status in ["finished", "completed", "resolved", "success"]:
            pr_info = data.get("pull_request", {})
            pr_url = pr_info.get("url", "No PR URL provided")
            return "COMPLETED", f"PR Created: {pr_url}"
            
        # Expanded failure/blocked conditions
        elif current_status in ["expired", "failed", "error", "stopped", "blocked", "requires_action"]:
            return "FAILED", f"Devin stopped with status: {current_status}"
            
        time.sleep(30)
        
    return "TIMEOUT", "Orchestrator stopped waiting after 15 minutes."