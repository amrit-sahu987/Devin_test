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
