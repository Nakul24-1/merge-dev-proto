from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class WorkExperience(BaseModel):
    job_title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class Education(BaseModel):
    degree: str
    institution: str
    graduation_date: Optional[str] = None
    field_of_study: Optional[str] = None

class Candidate(BaseModel):
    id: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_job_title: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    years_of_experience: Optional[int] = None
    resume_text: Optional[str] = None

class JobDescription(BaseModel):
    id: Optional[str] = None
    title: str
    company: Optional[str] = None
    description: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    education_requirements: Optional[str] = None
    experience_requirements: Optional[str] = None
    location: Optional[str] = None

class ScreeningQuestion(BaseModel):
    question: str
    category: str  # e.g., "skills", "experience", "motivation", "verification"
    source: Optional[str] = None  # e.g., "resume", "job_description"

class CallRequest(BaseModel):
    candidate_id: str
    job_id: str
    # ElevenLabs config - these can be set via environment or passed per request
    agent_id: Optional[str] = None  # ElevenLabs Agent ID
    agent_phone_number_id: Optional[str] = None  # Twilio phone number ID in ElevenLabs

class CallStatus(BaseModel):
    call_id: str
    candidate_id: str
    status: str  # e.g., "pending", "initiated", "in_progress", "completed", "failed"
    conversation_id: Optional[str] = None  # ElevenLabs conversation ID
    call_sid: Optional[str] = None  # Twilio call SID
    questions_asked: List[ScreeningQuestion] = Field(default_factory=list)
    transcript: Optional[str] = None
    summary: Optional[str] = None

