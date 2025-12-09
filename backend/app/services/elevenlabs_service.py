"""
ElevenLabs Telephony Service

Handles outbound calls via ElevenLabs Agents Platform + Twilio integration.
"""

import os
import httpx
from typing import Optional
from pydantic import BaseModel

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"


class OutboundCallRequest(BaseModel):
    agent_id: str
    agent_phone_number_id: str
    to_number: str
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    # Dynamic variables to pass to the agent
    dynamic_variables: Optional[dict] = None


class OutboundCallResponse(BaseModel):
    success: bool
    message: str
    conversation_id: Optional[str] = None
    call_sid: Optional[str] = None


async def initiate_outbound_call(
    agent_id: str,
    agent_phone_number_id: str,
    to_number: str,
    candidate_name: Optional[str] = None,
    job_title: Optional[str] = None,
    candidate_skills: Optional[list] = None,
    custom_first_message: Optional[str] = None,
    dynamic_variables: Optional[dict] = None,
) -> OutboundCallResponse:
    """
    Initiate an outbound call via ElevenLabs Twilio integration.
    
    Args:
        agent_id: ElevenLabs Agent ID
        agent_phone_number_id: Twilio phone number ID configured in ElevenLabs
        to_number: Candidate's phone number to call
        candidate_name: Candidate's name for personalization
        job_title: Job title being screened for
        candidate_skills: List of candidate's skills
        custom_first_message: Override the first message
        dynamic_variables: Additional dynamic variables for the agent
    
    Returns:
        OutboundCallResponse with conversation_id and call_sid
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return OutboundCallResponse(
            success=False,
            message="ELEVENLABS_API_KEY not configured",
            conversation_id=None,
            call_sid=None
        )
    
    # Build dynamic variables for personalization
    variables = dynamic_variables or {}
    if candidate_name:
        variables["candidate_name"] = candidate_name
    if job_title:
        variables["job_title"] = job_title
    if candidate_skills:
        variables["candidate_skills"] = ", ".join(candidate_skills[:5])  # Top 5 skills
    
    # Build conversation config override
    conversation_config_override = {}
    if custom_first_message:
        conversation_config_override["agent"] = {
            "first_message": custom_first_message
        }
    
    # Build request payload
    payload = {
        "agent_id": agent_id,
        "agent_phone_number_id": agent_phone_number_id,
        "to_number": to_number,
    }
    
    # Add conversation initiation data if we have overrides or variables
    if variables or conversation_config_override:
        payload["conversation_initiation_client_data"] = {}
        if variables:
            payload["conversation_initiation_client_data"]["dynamic_variables"] = variables
        if conversation_config_override:
            payload["conversation_initiation_client_data"]["conversation_config_override"] = conversation_config_override
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ELEVENLABS_API_URL}/convai/twilio/outbound-call",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "xi-api-key": api_key,
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return OutboundCallResponse(
                    success=data.get("success", False),
                    message=data.get("message", "Call initiated"),
                    conversation_id=data.get("conversation_id"),
                    call_sid=data.get("callSid")
                )
            else:
                return OutboundCallResponse(
                    success=False,
                    message=f"API error: {response.status_code} - {response.text}",
                    conversation_id=None,
                    call_sid=None
                )
        except Exception as e:
            return OutboundCallResponse(
                success=False,
                message=f"Request failed: {str(e)}",
                conversation_id=None,
                call_sid=None
            )


async def get_conversation_details(conversation_id: str) -> dict:
    """
    Get conversation details from ElevenLabs API.
    
    Args:
        conversation_id: The conversation ID from an outbound call
    
    Returns:
        Conversation details including transcript, status, etc.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {"error": "ELEVENLABS_API_KEY not configured"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ELEVENLABS_API_URL}/convai/conversations/{conversation_id}",
                headers={
                    "xi-api-key": api_key,
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
