// Type definitions matching backend Pydantic models

export interface WorkExperience {
    job_title: string;
    company: string;
    start_date?: string;
    end_date?: string;
    description?: string;
}

export interface Education {
    degree: string;
    institution: string;
    graduation_date?: string;
    field_of_study?: string;
}

export interface Candidate {
    id?: string;
    full_name: string;
    email?: string;
    phone?: string;
    current_job_title?: string;
    current_company?: string;
    location?: string;
    skills: string[];
    certifications: string[];
    work_experience: WorkExperience[];
    education: Education[];
    years_of_experience?: number;
    resume_text?: string;
}

export interface JobDescription {
    id?: string;
    title: string;
    company?: string;
    description: string;
    required_skills: string[];
    preferred_skills: string[];
    education_requirements?: string;
    experience_requirements?: string;
    location?: string;
}

export interface ScreeningQuestion {
    question: string;
    category: string;
    source?: string;
}

export interface CallRequest {
    candidate_id: string;
    job_id: string;
    agent_id?: string;  // ElevenLabs Agent ID (optional, can use env default)
    agent_phone_number_id?: string;  // Twilio phone number ID in ElevenLabs
}

export interface CallStatus {
    call_id: string;
    candidate_id: string;
    status: 'pending' | 'initiated' | 'in_progress' | 'completed' | 'failed';
    conversation_id?: string;  // ElevenLabs conversation ID
    call_sid?: string;  // Twilio call SID
    questions_asked: ScreeningQuestion[];
    transcript?: string;
    summary?: string;
}

