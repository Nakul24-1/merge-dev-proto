from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import os

from app.models.schemas import Candidate, JobDescription, CallRequest, CallStatus, ScreeningQuestion
from app.services.resume_parser import parse_resume
from app.services.screening_service import generate_screening_questions
from app.services.elevenlabs_service import initiate_outbound_call, get_conversation_details
from app.api.endpoints.webhooks import register_candidate_phone

router = APIRouter(prefix="/candidates", tags=["Candidates"])

# In-memory storage for demo purposes
candidates_db: dict[str, Candidate] = {}
jobs_db: dict[str, JobDescription] = {}
calls_db: dict[str, CallStatus] = {}

@router.post("/upload-resume", response_model=Candidate)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF or DOCX) and parse it to extract candidate data.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt"]
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not supported. Allowed: {allowed_extensions}")
    
    content = await file.read()
    
    # Parse the resume
    candidate = await parse_resume(content, file.filename)
    candidate.id = str(uuid.uuid4())
    
    # Store in our in-memory db
    candidates_db[candidate.id] = candidate
    
    return candidate

@router.get("/", response_model=List[Candidate])
async def list_candidates():
    """
    List all uploaded candidates.
    """
    return list(candidates_db.values())

@router.get("/{candidate_id}", response_model=Candidate)
async def get_candidate(candidate_id: str):
    """
    Get a specific candidate by ID.
    """
    if candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidates_db[candidate_id]

@router.post("/jobs", response_model=JobDescription)
async def create_job(job: JobDescription):
    """
    Create a new job description for screening.
    """
    job.id = str(uuid.uuid4())
    jobs_db[job.id] = job
    return job

@router.get("/jobs/", response_model=List[JobDescription])
async def list_jobs():
    """
    List all job descriptions.
    """
    return list(jobs_db.values())

@router.post("/generate-questions", response_model=List[ScreeningQuestion])
async def generate_questions(candidate_id: str, job_id: str):
    """
    Generate screening questions based on candidate resume and job description.
    """
    if candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = candidates_db[candidate_id]
    job = jobs_db[job_id]
    
    questions = await generate_screening_questions(candidate, job)
    return questions

@router.post("/initiate-call", response_model=CallStatus)
async def initiate_call(request: CallRequest):
    """
    Initiate a screening call to the candidate via ElevenLabs + Twilio.
    
    Requires environment variables:
    - ELEVENLABS_API_KEY: Your ElevenLabs API key
    - ELEVENLABS_AGENT_ID: Default agent ID (can be overridden in request)
    - ELEVENLABS_PHONE_NUMBER_ID: Default Twilio phone number ID (can be overridden)
    """
    if request.candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if request.job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = candidates_db[request.candidate_id]
    job = jobs_db[request.job_id]
    
    # Validate phone number
    if not candidate.phone:
        raise HTTPException(status_code=400, detail="Candidate has no phone number")
    
    # Get ElevenLabs config from request or environment
    agent_id = request.agent_id or os.getenv("ELEVENLABS_AGENT_ID")
    phone_number_id = request.agent_phone_number_id or os.getenv("ELEVENLABS_PHONE_NUMBER_ID")
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required (set ELEVENLABS_AGENT_ID env var or pass in request)")
    if not phone_number_id:
        raise HTTPException(status_code=400, detail="agent_phone_number_id required (set ELEVENLABS_PHONE_NUMBER_ID env var or pass in request)")
    
    # Register candidate phone for inbound call recognition
    register_candidate_phone(candidate.phone, {
        "full_name": candidate.full_name,
        "job_title": job.title,
        "skills": candidate.skills,
        "candidate_id": request.candidate_id,
        "job_id": request.job_id,
    })
    
    # Generate a custom first message
    first_message = f"Hi {candidate.full_name}! This is a call regarding your application for the {job.title} position. I'm an AI assistant and I'll be asking you a few screening questions. Is now a good time to talk?"
    
    # Make the outbound call via ElevenLabs
    result = await initiate_outbound_call(
        agent_id=agent_id,
        agent_phone_number_id=phone_number_id,
        to_number=candidate.phone,
        candidate_name=candidate.full_name,
        job_title=job.title,
        candidate_skills=candidate.skills,
        custom_first_message=first_message,
    )
    
    # Create call status record
    call_id = str(uuid.uuid4())
    call_status = CallStatus(
        call_id=call_id,
        candidate_id=request.candidate_id,
        status="initiated" if result.success else "failed",
        conversation_id=result.conversation_id,
        call_sid=result.call_sid,
        questions_asked=[],  # Questions handled by ElevenLabs agent prompt
        transcript=None,
        summary=result.message if not result.success else None
    )
    
    calls_db[call_id] = call_status
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return call_status

@router.get("/calls/{call_id}", response_model=CallStatus)
async def get_call_status(call_id: str):
    """
    Get the status of a screening call.
    """
    if call_id not in calls_db:
        raise HTTPException(status_code=404, detail="Call not found")
    return calls_db[call_id]

@router.get("/calls/{call_id}/details")
async def get_call_details(call_id: str):
    """
    Get detailed conversation data from ElevenLabs (transcript, etc.)
    """
    if call_id not in calls_db:
        raise HTTPException(status_code=404, detail="Call not found")
    
    call = calls_db[call_id]
    if not call.conversation_id:
        raise HTTPException(status_code=400, detail="No conversation ID for this call")
    
    details = await get_conversation_details(call.conversation_id)
    return details

