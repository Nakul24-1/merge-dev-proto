"""
Webhooks for ElevenLabs Agents Platform

Handles:
- Inbound call personalization webhook (Twilio)
- Call status webhooks (optional)
"""

from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# In-memory storage - in production, use a database
# Maps phone numbers to candidate data
phone_to_candidate: dict = {}


class TwilioInboundWebhookRequest(BaseModel):
    caller_id: str
    agent_id: str
    called_number: str
    call_sid: str


class ConversationInitiationResponse(BaseModel):
    type: str = "conversation_initiation_client_data"
    dynamic_variables: dict
    conversation_config_override: Optional[dict] = None


@router.post("/elevenlabs/twilio-inbound")
async def handle_twilio_inbound_webhook(
    request: Request,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    Webhook endpoint for ElevenLabs to fetch conversation initiation data
    for inbound Twilio calls.
    
    This endpoint is called when a candidate calls back the screening number.
    It looks up the caller's phone number and returns personalization data.
    """
    # Validate webhook secret if configured
    expected_secret = os.getenv("ELEVENLABS_WEBHOOK_SECRET")
    if expected_secret and x_webhook_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    body = await request.json()
    caller_id = body.get("caller_id", "")
    agent_id = body.get("agent_id", "")
    called_number = body.get("called_number", "")
    call_sid = body.get("call_sid", "")
    
    # Normalize phone number for lookup (remove formatting)
    normalized_phone = normalize_phone(caller_id)
    
    # Look up candidate by phone number
    candidate_data = phone_to_candidate.get(normalized_phone)
    
    if candidate_data:
        # Found matching candidate - return personalized data
        return {
            "type": "conversation_initiation_client_data",
            "dynamic_variables": {
                "candidate_name": candidate_data.get("full_name", "there"),
                "job_title": candidate_data.get("job_title", "the position"),
                "candidate_skills": ", ".join(candidate_data.get("skills", [])[:3]),
                "is_returning_call": "true",
            },
            "conversation_config_override": {
                "agent": {
                    "first_message": f"Hi {candidate_data.get('full_name', 'there')}! Thanks for returning our call about the {candidate_data.get('job_title', 'position')}. I'm ready to continue with your screening whenever you are. Shall we begin?"
                }
            }
        }
    else:
        # Unknown caller - use generic greeting
        return {
            "type": "conversation_initiation_client_data",
            "dynamic_variables": {
                "candidate_name": "there",
                "is_returning_call": "false",
            },
            "conversation_config_override": {
                "agent": {
                    "first_message": "Hello! Thank you for calling our recruitment line. Are you calling about a recent job application? Could I have your name please?"
                }
            }
        }


def normalize_phone(phone: str) -> str:
    """Normalize phone number for consistent lookup."""
    # Remove all non-digit characters except +
    return ''.join(c for c in phone if c.isdigit() or c == '+')


def register_candidate_phone(phone: str, candidate_data: dict):
    """
    Register a candidate's phone number for inbound call recognition.
    Called when we make an outbound call to a candidate.
    """
    normalized = normalize_phone(phone)
    phone_to_candidate[normalized] = candidate_data


def get_candidate_by_phone(phone: str) -> Optional[dict]:
    """Look up candidate data by phone number."""
    normalized = normalize_phone(phone)
    return phone_to_candidate.get(normalized)
