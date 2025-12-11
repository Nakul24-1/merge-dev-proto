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
    company_name: Optional[str] = None,
    candidate_skills: Optional[list] = None,
    resume_text: Optional[str] = None,  # Kept for storage, but structured data preferred
    job_description: Optional[str] = None,
    custom_first_message: Optional[str] = None,
    dynamic_variables: Optional[dict] = None,
    # New structured data fields
    candidate_summary: Optional[str] = None,
    work_experience: Optional[list] = None,
    education: Optional[list] = None,
    certifications: Optional[list] = None,
    years_of_experience: Optional[int] = None,
    current_job_title: Optional[str] = None,
    current_company: Optional[str] = None,
) -> OutboundCallResponse:
    """
    Initiate an outbound call using ElevenLabs Conversational AI + Twilio.
    """
    # Get API key from environment
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
    if company_name:
        variables["company_name"] = company_name
    if candidate_skills:
        variables["candidate_skills"] = ", ".join(candidate_skills[:10])
    if job_description:
        variables["job_description"] = job_description[:4000] if len(job_description) > 4000 else job_description
    
    # Add structured candidate context (preferred over raw resume for better LLM understanding)
    if candidate_summary:
        variables["candidate_summary"] = candidate_summary[:2000]
    if years_of_experience:
        variables["years_of_experience"] = str(years_of_experience)
    if current_job_title:
        variables["current_job_title"] = current_job_title
    if current_company:
        variables["current_company"] = current_company
    if certifications:
        variables["certifications"] = ", ".join(certifications[:5])
    
    # Format work experience as readable text for LLM
    if work_experience:
        exp_text = []
        for exp in work_experience[:5]:  # Limit to last 5 positions
            if isinstance(exp, dict):
                exp_line = f"{exp.get('job_title', 'Unknown')} at {exp.get('company', 'Unknown')}"
                if exp.get('start_date') or exp.get('end_date'):
                    exp_line += f" ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})"
                if exp.get('description'):
                    exp_line += f": {exp['description'][:200]}"
                exp_text.append(exp_line)
        if exp_text:
            variables["work_experience"] = " | ".join(exp_text)[:3000]
    
    # Format education as readable text for LLM
    if education:
        edu_text = []
        for edu in education[:3]:  # Limit to 3 entries
            if isinstance(edu, dict):
                edu_line = f"{edu.get('degree', 'Degree')} from {edu.get('institution', 'Institution')}"
                if edu.get('field_of_study'):
                    edu_line += f" in {edu['field_of_study']}"
                if edu.get('graduation_date'):
                    edu_line += f" ({edu['graduation_date']})"
                edu_text.append(edu_line)
        if edu_text:
            variables["education"] = " | ".join(edu_text)
    
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
