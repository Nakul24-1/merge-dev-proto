"""
Test script to create a candidate, job, and initiate a call
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Test resume content
TEST_RESUME = """
John Smith
Senior Software Engineer

Email: john.smith@email.com
Phone: +1 347 669 0154
Location: New York, NY

SUMMARY
Experienced software engineer with 8+ years in full-stack development.
Passionate about building scalable applications and mentoring junior developers.

SKILLS
Python, JavaScript, React, Node.js, AWS, Docker, PostgreSQL, Redis, FastAPI

EXPERIENCE

Senior Software Engineer | TechCorp Inc | 2020-Present
- Led development of microservices architecture serving 1M+ users
- Reduced API latency by 40% through optimization
- Mentored team of 5 junior developers

Software Engineer | StartupXYZ | 2017-2020
- Built real-time analytics dashboard using React and D3.js
- Implemented CI/CD pipeline using GitHub Actions
- Developed RESTful APIs with Python Flask

EDUCATION
BS Computer Science | NYU | 2017
"""

def test_call():
    print("1. Creating test candidate...")
    
    # Create candidate via upload
    files = {'file': ('resume.txt', TEST_RESUME, 'text/plain')}
    data = {'phone': '+13476690154'}
    
    resp = requests.post(f"{BASE_URL}/candidates/upload-resume", files=files, data=data)
    if resp.status_code != 200:
        print(f"   ❌ Failed to create candidate: {resp.text}")
        return
    
    candidate = resp.json()
    candidate_id = candidate['id']
    print(f"   ✅ Candidate created: {candidate['full_name']} (ID: {candidate_id})")
    
    print("\n2. Creating test job...")
    
    job_data = {
        "title": "Senior Software Engineer",
        "company": "Acme Corp",
        "description": "We're looking for a senior software engineer to join our team.",
        "requirements": ["Python", "React", "AWS", "5+ years experience"],
        "preferred_skills": ["Docker", "Kubernetes", "PostgreSQL"]
    }
    
    resp = requests.post(f"{BASE_URL}/candidates/jobs", json=job_data)
    if resp.status_code != 200:
        print(f"   ❌ Failed to create job: {resp.text}")
        return
    
    job = resp.json()
    job_id = job['id']
    print(f"   ✅ Job created: {job['title']} at {job['company']} (ID: {job_id})")
    
    print("\n3. Initiating screening call...")
    print(f"   📞 Calling +1 347 669 0154...")
    
    call_data = {
        "candidate_id": candidate_id,
        "job_id": job_id
    }
    
    resp = requests.post(f"{BASE_URL}/candidates/initiate-call", json=call_data)
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"\n   ✅ Call initiated!")
        print(f"   Call ID: {result.get('call_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Conversation ID: {result.get('conversation_id')}")
        print(f"   Twilio SID: {result.get('call_sid')}")
    else:
        print(f"\n   ❌ Failed to initiate call: {resp.status_code}")
        print(f"   Error: {resp.text}")

if __name__ == "__main__":
    test_call()
