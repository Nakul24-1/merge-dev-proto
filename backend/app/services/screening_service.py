"""
Screening Service

Generates personalized screening questions based on candidate resume and job description.
Uses AI/LLM for intelligent question generation.
"""

from typing import List
from app.models.schemas import Candidate, JobDescription, ScreeningQuestion
import os


async def generate_screening_questions(
    candidate: Candidate, 
    job: JobDescription
) -> List[ScreeningQuestion]:
    """
    Generate tailored screening questions based on candidate profile and job requirements.
    
    Args:
        candidate: Parsed candidate data from resume
        job: Job description with requirements
    
    Returns:
        List of screening questions categorized by type
    """
    questions: List[ScreeningQuestion] = []
    
    # 1. Verification Questions - Confirm resume details
    questions.extend(generate_verification_questions(candidate, job))
    
    # 2. Skills Assessment Questions - Probe claimed skills
    questions.extend(generate_skill_questions(candidate, job))
    
    # 3. Experience Questions - Dig into work history
    questions.extend(generate_experience_questions(candidate, job))
    
    # 4. Role Fit Questions - Assess motivation and understanding
    questions.extend(generate_role_fit_questions(candidate, job))
    
    # 5. Gap/Anomaly Questions - Address any inconsistencies
    questions.extend(generate_gap_questions(candidate, job))
    
    return questions


def generate_verification_questions(
    candidate: Candidate, 
    job: JobDescription
) -> List[ScreeningQuestion]:
    """Generate questions to verify resume information."""
    questions = []
    
    if candidate.current_job_title:
        questions.append(ScreeningQuestion(
            question=f"Can you confirm your current role as {candidate.current_job_title}?",
            category="verification",
            source="resume"
        ))
    
    if candidate.years_of_experience:
        questions.append(ScreeningQuestion(
            question=f"Your resume indicates about {candidate.years_of_experience} years of experience. Is that accurate?",
            category="verification",
            source="resume"
        ))
    
    if candidate.location and job.location:
        questions.append(ScreeningQuestion(
            question=f"The role is based in {job.location}. You're currently in {candidate.location}. Would you be open to relocating or is remote work preferred?",
            category="verification",
            source="job_description"
        ))
    
    return questions


def generate_skill_questions(
    candidate: Candidate, 
    job: JobDescription
) -> List[ScreeningQuestion]:
    """Generate questions about specific skills."""
    questions = []
    
    # Find overlapping skills between candidate and job requirements
    candidate_skills_lower = [s.lower() for s in candidate.skills]
    
    for required_skill in job.required_skills[:3]:  # Limit to top 3
        if required_skill.lower() in candidate_skills_lower:
            questions.append(ScreeningQuestion(
                question=f"I see you have experience with {required_skill}. Can you describe a project where you used this skill and what your specific contribution was?",
                category="skills",
                source="resume"
            ))
        else:
            questions.append(ScreeningQuestion(
                question=f"This role requires {required_skill}. Do you have any experience with this, or related technologies?",
                category="skills",
                source="job_description"
            ))
    
    return questions


def generate_experience_questions(
    candidate: Candidate, 
    job: JobDescription
) -> List[ScreeningQuestion]:
    """Generate questions about work experience."""
    questions = []
    
    if candidate.work_experience:
        latest_job = candidate.work_experience[0]
        questions.append(ScreeningQuestion(
            question=f"Tell me about your role at {latest_job.company}. What were your main responsibilities?",
            category="experience",
            source="resume"
        ))
    
    # General experience question related to the job
    questions.append(ScreeningQuestion(
        question=f"What experience do you have that's most relevant to the {job.title} position?",
        category="experience",
        source="job_description"
    ))
    
    return questions


def generate_role_fit_questions(
    candidate: Candidate, 
    job: JobDescription
) -> List[ScreeningQuestion]:
    """Generate questions to assess role understanding and motivation."""
    questions = []
    
    questions.append(ScreeningQuestion(
        question=f"What attracted you to apply for the {job.title} role at {job.company or 'our company'}?",
        category="motivation",
        source="job_description"
    ))
    
    questions.append(ScreeningQuestion(
        question="Where do you see yourself in 2-3 years, and how does this role fit into that?",
        category="motivation",
        source="general"
    ))
    
    # Check for potential career pivots
    if candidate.current_job_title and job.title:
        candidate_title_lower = candidate.current_job_title.lower()
        job_title_lower = job.title.lower()
        
        # Simple check for different domains
        if not any(word in job_title_lower for word in candidate_title_lower.split()):
            questions.append(ScreeningQuestion(
                question=f"Your background is in {candidate.current_job_title}, but you're applying for {job.title}. What's driving this career transition?",
                category="motivation",
                source="resume"
            ))
    
    return questions


def generate_gap_questions(
    candidate: Candidate, 
    job: JobDescription
) -> List[ScreeningQuestion]:
    """Generate questions about employment gaps or anomalies."""
    questions = []
    
    # This would require more sophisticated gap detection in production
    # For now, add a general availability question
    questions.append(ScreeningQuestion(
        question="What is your availability to start? Are you currently in a notice period?",
        category="logistics",
        source="general"
    ))
    
    return questions


async def generate_ai_questions(
    candidate: Candidate, 
    job: JobDescription
) -> List[ScreeningQuestion]:
    """
    Use AI/LLM to generate more sophisticated questions.
    This is a placeholder for OpenAI or other LLM integration.
    """
    # TODO: Integrate with OpenAI API for more intelligent question generation
    # Example prompt:
    # "Given this candidate resume: {candidate.resume_text}
    #  And this job description: {job.description}
    #  Generate 5 targeted screening questions to assess fit."
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fall back to rule-based questions if no API key
        return []
    
    # OpenAI integration would go here
    return []
