from app.services.resume_parser import extract_candidate_data

SAMPLE_RESUME = """
John Doe
Software Engineer
john.doe@example.com
(555) 123-4567

Summary:
Experienced developer with 5+ years of experience in Python and React.
Currently working at TechCorp as a Senior Developer.

Experience:
Senior Developer
TechCorp
2020 - Present

Skills:
Python, React, Docker, AWS, SQL
"""

def test_parser():
    print("Testing Resume Parser...")
    candidate = extract_candidate_data(SAMPLE_RESUME)
    
    print(f"Name: {candidate.full_name}")
    print(f"Email: {candidate.email}")
    print(f"Phone: {candidate.phone}")
    print(f"Title: {candidate.current_job_title}")
    print(f"Exp: {candidate.years_of_experience}")
    print(f"Skills: {candidate.skills}")
    
    # Assertions
    assert candidate.full_name == "John Doe"
    assert candidate.email == "john.doe@example.com"
    assert candidate.phone == "(555) 123-4567"
    assert "Python" in candidate.skills
    assert candidate.years_of_experience >= 5
    
    print("✅ Parser Logic Verified!")

if __name__ == "__main__":
    test_parser()
