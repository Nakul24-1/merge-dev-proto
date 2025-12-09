"""
Resume Parser Service

Parses uploaded resume files and extracts structured candidate data.
Uses a simple text extraction approach. For production, integrate with
specialized parsing libraries (PyPDF2, python-docx) or AI-based extraction.
"""

from app.models.schemas import Candidate, WorkExperience, Education
import re


async def parse_resume(content: bytes, filename: str) -> Candidate:
    """
    Parse a resume file and extract candidate information.
    
    Args:
        content: Raw bytes of the uploaded file
        filename: Name of the file for extension detection
    
    Returns:
        Candidate object with extracted data
    """
    # Extract text from the file
    text = extract_text(content, filename)
    
    # Parse the extracted text
    candidate = extract_candidate_data(text)
    candidate.resume_text = text
    
    return candidate


def extract_text(content: bytes, filename: str) -> str:
    """
    Extract text from the resume file based on its type.
    """
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    if ext == "txt":
        return content.decode("utf-8", errors="ignore")
    elif ext == "pdf":
        # For PDF parsing, you would typically use PyPDF2 or pdfplumber
        # For now, we'll return a placeholder and decode what we can
        try:
            # Attempt basic text extraction (works for text-based PDFs)
            text = content.decode("utf-8", errors="ignore")
            # Filter to printable characters
            text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")
            return text if len(text) > 50 else "[PDF content - requires PyPDF2 for full extraction]"
        except Exception:
            return "[PDF content - requires PyPDF2 for full extraction]"
    elif ext in ["doc", "docx"]:
        # For DOCX, you would use python-docx
        try:
            text = content.decode("utf-8", errors="ignore")
            text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")
            return text if len(text) > 50 else "[DOCX content - requires python-docx for full extraction]"
        except Exception:
            return "[DOCX content - requires python-docx for full extraction]"
    else:
        return content.decode("utf-8", errors="ignore")


def extract_candidate_data(text: str) -> Candidate:
    """
    Extract structured candidate data from resume text.
    Uses regex patterns and heuristics. For production, use AI/NLP.
    """
    # Initialize with defaults
    candidate = Candidate(full_name="Unknown")
    
    lines = text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    
    # Try to extract name (usually first line or after "Name:")
    if lines:
        first_meaningful_line = lines[0]
        # Check if it looks like a name (2-4 words, no special chars)
        if re.match(r"^[A-Za-z\s]{3,50}$", first_meaningful_line):
            candidate.full_name = first_meaningful_line.title()
    
    # Extract email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, text)
    if emails:
        candidate.email = emails[0]
    
    # Extract phone number
    phone_pattern = r"[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}"
    phones = re.findall(phone_pattern, text)
    if phones:
        # Get the longest match (most likely a full phone number)
        candidate.phone = max(phones, key=len)
    
    # Extract skills (look for common skill keywords)
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Angular", "Vue",
        "Node.js", "SQL", "PostgreSQL", "MySQL", "MongoDB", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "Git", "Agile", "Scrum", "Project Management",
        "Machine Learning", "AI", "Data Science", "Excel", "PowerPoint", "Word",
        "Salesforce", "HubSpot", "Marketing", "Sales", "Leadership", "Communication"
    ]
    found_skills = []
    text_lower = text.lower()
    for skill in common_skills:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    candidate.skills = found_skills
    
    # Try to extract years of experience
    exp_pattern = r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)"
    exp_matches = re.findall(exp_pattern, text_lower)
    if exp_matches:
        candidate.years_of_experience = int(exp_matches[0])
    
    # Extract location (look for common patterns)
    location_patterns = [
        r"(?:Location|Address|City)[\s:]+([A-Za-z\s,]+)",
        r"([A-Za-z\s]+,\s*[A-Z]{2})",  # City, ST format
    ]
    for pattern in location_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            candidate.location = matches[0].strip()
            break
    
    return candidate
