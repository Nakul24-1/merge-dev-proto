"""
Resume Parser Service

Parses uploaded resume files using LlamaCloud's LlamaExtract for accurate
structured data extraction.
"""

from fastapi import HTTPException
from app.models.schemas import Candidate, WorkExperience, Education
from app.services.llama_parser import parse_resume_with_llama, ResumeSchema


async def parse_resume(content: bytes, filename: str) -> Candidate:
    """
    Parse a resume file and extract candidate information using LlamaParse.
    
    Args:
        content: Raw bytes of the uploaded file
        filename: Name of the file for extension detection
    
    Returns:
        Candidate object with extracted data
        
    Raises:
        HTTPException: If parsing fails (no fallback, shows error to user)
    """
    try:
        # Parse using LlamaParse
        parsed: ResumeSchema = await parse_resume_with_llama(content, filename)
        
        # Convert work experience
        work_experience = []
        for exp in parsed.work_experience:
            work_experience.append(WorkExperience(
                job_title=exp.job_title,
                company=exp.company,
                start_date=exp.start_date,
                end_date=exp.end_date,
                description=exp.description
            ))
        
        # Convert education
        education = []
        for edu in parsed.education:
            education.append(Education(
                degree=edu.degree,
                institution=edu.institution,
                graduation_date=edu.graduation_date,
                field_of_study=edu.field_of_study
            ))
        
        # Extract raw text for future LLM use
        raw_text = extract_raw_text(content, filename)
        
        # Build Candidate model
        candidate = Candidate(
            full_name=parsed.full_name or "Unknown",
            email=parsed.email,
            phone=parsed.phone,
            current_job_title=parsed.current_job_title,
            current_company=parsed.current_company,
            location=parsed.location,
            skills=parsed.skills or [],
            certifications=parsed.certifications or [],
            years_of_experience=parsed.years_of_experience,
            work_experience=work_experience,
            education=education,
            summary=parsed.summary,
            resume_text=raw_text,  # Store raw text for future use
        )
        
        return candidate
        
    except ValueError as e:
        # Configuration errors (missing API key, etc.)
        raise HTTPException(
            status_code=500,
            detail=f"Resume parsing configuration error: {str(e)}"
        )
    except Exception as e:
        # Parsing errors
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse resume: {str(e)}. Please ensure the file is a valid resume document."
        )


def extract_raw_text(content: bytes, filename: str) -> str:
    """
    Extract raw text from the resume file for storage.
    Uses basic text extraction - the structured data comes from LlamaParse.
    """
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    if ext == "txt":
        return content.decode("utf-8", errors="ignore")
    elif ext == "pdf":
        try:
            # Basic text extraction for PDFs
            text = content.decode("utf-8", errors="ignore")
            text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")
            if len(text) > 50:
                return text
            return "[PDF content - raw text extraction limited]"
        except Exception:
            return "[PDF content]"
    elif ext in ["doc", "docx"]:
        try:
            text = content.decode("utf-8", errors="ignore")
            text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")
            if len(text) > 50:
                return text
            return "[DOCX content - raw text extraction limited]"
        except Exception:
            return "[DOCX content]"
    else:
        return content.decode("utf-8", errors="ignore")
