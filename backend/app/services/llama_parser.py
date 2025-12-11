"""
LlamaParse Resume Parser Service

Uses LlamaCloud's LlamaExtract for structured resume parsing.
"""

import os
import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class WorkExperienceExtracted(BaseModel):
    """Work experience entry extracted from resume."""
    job_title: str = Field(default="", description="Job title/position")
    company: str = Field(default="", description="Company name")
    start_date: Optional[str] = Field(default=None, description="Start date (e.g. 'January 2020', 'Jan 2020', '2020')")
    end_date: Optional[str] = Field(default=None, description="End date (e.g. 'March 2023', 'Present', 'Current')")
    description: Optional[str] = Field(default=None, description="Job responsibilities and achievements")


class EducationExtracted(BaseModel):
    """Education entry extracted from resume."""
    degree: str = Field(default="", description="Degree obtained")
    institution: str = Field(default="", description="School/University name")
    graduation_date: Optional[str] = Field(default=None, description="Graduation date")
    field_of_study: Optional[str] = Field(default=None, description="Major/Field of study")


class ResumeSchema(BaseModel):
    """Complete resume schema for LlamaExtract parsing."""
    full_name: str = Field(default="Unknown", description="Full name of the candidate")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Location/Address")
    current_job_title: Optional[str] = Field(default=None, description="Current or most recent job title")
    current_company: Optional[str] = Field(default=None, description="Current or most recent company")
    summary: Optional[str] = Field(default=None, description="Professional summary or objective")
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    certifications: List[str] = Field(default_factory=list, description="List of certifications")
    years_of_experience: Optional[int] = Field(
        default=None, 
        description="CALCULATE the total years of professional work experience by analyzing the start and end dates of all work experience entries. Sum up the duration of each job. If 'Present' or 'Current', use today's date."
    )
    work_experience: List[WorkExperienceExtracted] = Field(default_factory=list, description="List of all work experiences with dates")
    education: List[EducationExtracted] = Field(default_factory=list, description="List of education")


# Global agent cache to avoid recreating on each request
_resume_agent = None


def get_resume_agent():
    """Get or create the resume parsing agent."""
    global _resume_agent
    
    if _resume_agent is not None:
        return _resume_agent
    
    from llama_cloud_services import LlamaExtract
    
    api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY environment variable is not set")
    
    extractor = LlamaExtract()
    
    # Try to get existing agent, create if not exists
    # Use v3 to force recreation with new schema
    try:
        agents = extractor.list_agents()
        for agent in agents:
            if agent.name == "resume-parser-v3":
                _resume_agent = agent
                return _resume_agent
    except Exception:
        pass
    
    # Create new agent with our schema
    _resume_agent = extractor.create_agent(
        name="resume-parser-v3",
        data_schema=ResumeSchema
    )
    
    return _resume_agent


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string into a datetime object."""
    if not date_str:
        return None
    
    date_str = date_str.strip().lower()
    
    # Handle "present", "current", "now"
    if date_str in ['present', 'current', 'now', 'ongoing']:
        return datetime.now()
    
    # Common date formats to try
    formats = [
        '%B %Y',      # January 2020
        '%b %Y',      # Jan 2020
        '%m/%Y',      # 01/2020
        '%Y-%m',      # 2020-01
        '%Y',         # 2020
        '%m-%Y',      # 01-2020
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.title(), fmt)
        except ValueError:
            continue
    
    # Try to extract year
    year_match = re.search(r'20\d{2}|19\d{2}', date_str)
    if year_match:
        try:
            return datetime(int(year_match.group()), 6, 1)  # Assume mid-year
        except:
            pass
    
    return None


def calculate_years_from_experience(work_experience: List[WorkExperienceExtracted]) -> int:
    """Calculate total years of experience from work history."""
    total_months = 0
    
    for exp in work_experience:
        start = parse_date(exp.start_date)
        end = parse_date(exp.end_date)
        
        if start and end:
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if months > 0:
                total_months += months
        elif start:
            # No end date, assume current
            end = datetime.now()
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if months > 0:
                total_months += months
    
    return max(1, total_months // 12) if total_months > 6 else 0


async def parse_resume_with_llama(content: bytes, filename: str) -> ResumeSchema:
    """
    Parse resume using LlamaCloud's LlamaExtract.
    
    Args:
        content: Raw bytes of the resume file
        filename: Original filename (for extension detection)
    
    Returns:
        ResumeSchema with extracted data
        
    Raises:
        ValueError: If API key is not configured
        Exception: If parsing fails
    """
    from llama_cloud_services.extract import SourceText
    
    agent = get_resume_agent()
    
    # Extract from bytes - using sync API since LlamaExtract handles it internally
    result = agent.extract(SourceText(file=content, filename=filename))
    
    if result.data is None:
        raise ValueError("LlamaParse returned no data for the resume")
    
    # result.data is a dict, convert to ResumeSchema
    data = result.data
    if isinstance(data, dict):
        schema = ResumeSchema(**data)
    else:
        schema = data
    
    # Post-process: Calculate years if LLM didn't or returned 0
    if not schema.years_of_experience or schema.years_of_experience == 0:
        if schema.work_experience:
            calculated_years = calculate_years_from_experience(schema.work_experience)
            if calculated_years > 0:
                schema.years_of_experience = calculated_years
    
    return schema

