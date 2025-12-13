from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import os

from app.models.schemas import Candidate, JobDescription, CallRequest, CallStatus, ScreeningQuestion
from app.services.resume_parser import parse_resume
from app.services.screening_service import generate_screening_questions
from app.services.elevenlabs_service import initiate_outbound_call, get_conversation_details
from app.api.endpoints.webhooks import register_candidate_phone
from app.db.database import (
    init_db, 
    seed_dummy_data, 
    get_all_candidates, 
    get_all_jobs, 
    get_candidate_by_id, 
    get_job_by_id,
    upsert_candidate,
    upsert_job,
    upsert_call,
    get_call_by_id,
    delete_candidate as db_delete_candidate,
    delete_job as db_delete_job
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])

# Database initialization moved to main.py startup event for faster server startup

# ============ CANDIDATE LIST ROUTES ============

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
    
    # Persist to DB
    candidate_dict = candidate.dict()
    upsert_candidate(candidate_dict)
    
    return candidate

@router.get("/", response_model=List[Candidate])
def list_candidates():
    """
    List all uploaded candidates.
    """
    candidates_data = get_all_candidates()
    return [Candidate(**c) for c in candidates_data]


# ============ JOB ROUTES (MUST BE BEFORE /{candidate_id}) ============

@router.post("/jobs", response_model=JobDescription)
def create_job(job: JobDescription):
    """
    Create a new job description for screening.
    """
    job.id = str(uuid.uuid4())
    upsert_job(job.dict())
    return job

@router.get("/jobs/", response_model=List[JobDescription])
def list_jobs():
    """
    List all job descriptions.
    """
    jobs_data = get_all_jobs()
    return [JobDescription(**j) for j in jobs_data]

@router.put("/jobs/{job_id}", response_model=JobDescription)
def update_job(job_id: str, job: JobDescription):
    """
    Update an existing job description.
    """
    job.id = job_id
    upsert_job(job.dict())
    return job

@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """
    Delete a job description by ID.
    """
    deleted = db_delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully", "id": job_id}


# ============ SCREENING ROUTES ============

@router.post("/generate-questions", response_model=List[ScreeningQuestion])
async def generate_questions(candidate_id: str, job_id: str):
    """
    Generate screening questions based on candidate resume and job description.
    """
    candidate_data = get_candidate_by_id(candidate_id)
    if not candidate_data:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    job_data = get_job_by_id(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = Candidate(**candidate_data)
    job = JobDescription(**job_data)
    
    questions = await generate_screening_questions(candidate, job)
    return questions

@router.post("/initiate-call", response_model=CallStatus)
async def initiate_call(request: CallRequest):
    """
    Initiate a screening call to the candidate via ElevenLabs + Twilio.
    """
    candidate_data = get_candidate_by_id(request.candidate_id)
    if not candidate_data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    job_data = get_job_by_id(request.job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = Candidate(**candidate_data)
    job = JobDescription(**job_data)
    
    phone_to_call = request.phone_override or candidate.phone
    
    if not phone_to_call:
        raise HTTPException(status_code=400, detail="No phone number available")
    
    agent_id = request.agent_id or os.getenv("ELEVENLABS_AGENT_ID")
    phone_number_id = request.agent_phone_number_id or os.getenv("ELEVENLABS_PHONE_NUMBER_ID")
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    if not phone_number_id:
        raise HTTPException(status_code=400, detail="agent_phone_number_id required")
    
    register_candidate_phone(phone_to_call, {
        "full_name": candidate.full_name,
        "job_title": job.title,
        "skills": candidate.skills,
        "candidate_id": request.candidate_id,
        "job_id": request.job_id,
    })
    
    first_message = f"Hi {candidate.full_name}! This is an AI assistant calling from {job.company or 'the hiring team'} regarding your application for the {job.title} position. Do you have about 5 to 10 minutes for a quick screening chat?"
    
    result = await initiate_outbound_call(
        agent_id=agent_id,
        agent_phone_number_id=phone_number_id,
        to_number=phone_to_call,
        candidate_name=candidate.full_name,
        job_title=job.title,
        company_name=job.company or "the hiring team",
        candidate_skills=candidate.skills,
        resume_text=candidate.resume_text,  # Still stored for future use
        job_description=job.description or str(job.required_skills),
        custom_first_message=first_message,
        # Pass structured data for better LLM understanding
        candidate_summary=candidate.summary,
        work_experience=[exp.dict() for exp in candidate.work_experience] if candidate.work_experience else None,
        education=[edu.dict() for edu in candidate.education] if candidate.education else None,
        certifications=candidate.certifications,
        years_of_experience=candidate.years_of_experience,
        current_job_title=candidate.current_job_title,
        current_company=candidate.current_company,
    )
    
    call_id = str(uuid.uuid4())
    call_status = CallStatus(
        call_id=call_id,
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        status="initiated" if result.success else "failed",
        conversation_id=result.conversation_id,
        call_sid=result.call_sid,
        questions_asked=[],
        transcript=None,
        summary=result.message if not result.success else None
    )
    
    upsert_call(call_status.dict())
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return call_status


# ============ CALL ROUTES ============

@router.get("/calls/{call_id}", response_model=CallStatus)
def get_call_status(call_id: str):
    """
    Get the status of a screening call.
    """
    call_data = get_call_by_id(call_id)
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")
    return CallStatus(**call_data)

@router.get("/calls/{call_id}/details")
async def get_call_details(call_id: str):
    """
    Get detailed conversation data from ElevenLabs.
    """
    call_data = get_call_by_id(call_id)
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")
    
    call = CallStatus(**call_data)
    if not call.conversation_id:
        raise HTTPException(status_code=400, detail="No conversation ID for this call")
    
    details = await get_conversation_details(call.conversation_id)
    return details


# ============ CANDIDATE BY ID ROUTES (MUST BE LAST - CATCH-ALL) ============

@router.get("/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: str):
    """
    Get a specific candidate by ID.
    """
    c_data = get_candidate_by_id(candidate_id)
    if not c_data:
         raise HTTPException(status_code=404, detail="Candidate not found")
    return Candidate(**c_data)

@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: str):
    """
    Delete a candidate by ID.
    """
    deleted = db_delete_candidate(candidate_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted successfully", "id": candidate_id}
