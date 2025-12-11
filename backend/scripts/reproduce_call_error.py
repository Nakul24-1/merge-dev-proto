import os
import requests
import json
from dotenv import load_dotenv

# Load env vars
load_dotenv(dotenv_path="../.env")

API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
PHONE_NUMBER_ID = os.getenv("ELEVENLABS_PHONE_NUMBER_ID")
TO_NUMBER = "+13476690154" 

# Payload matching the failing request
payload = {
    "agent_id": AGENT_ID,
    "agent_phone_number_id": PHONE_NUMBER_ID,
    "to_number": TO_NUMBER,
    "conversation_initiation_client_data": {
        "dynamic_variables": {
            "candidate_name": "John Test",
            "job_title": "Software Engineer",
            "company_name": "Test Corp",
            "candidate_skills": "Python, React",
            "resume_text": "Experienced developer..."
        },
        "conversation_config_override": {
            "agent": {
                "first_message": "Hi John! This is a test call."
            }
        }
    }
}

print(f"Sending payload to agent {AGENT_ID}...")
print(json.dumps(payload, indent=2))

response = requests.post(
    "https://api.elevenlabs.io/v1/convai/twilio/outbound-call",
    json=payload,
    headers={
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
)

print(f"\nStatus: {response.status_code}")
print(f"Response: {response.text}")
