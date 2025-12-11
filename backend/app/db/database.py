"""
Database module for PostgreSQL
"""
import os
import json
import uuid
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Global connection pool
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set")
        try:
            # Create a threaded connection pool
            # Min: 1, Max: 20 connections
            _pool = psycopg2.pool.ThreadedConnectionPool(1, 20, DATABASE_URL)
            print("✅ Database connection pool created")
        except Exception as e:
            print(f"❌ Failed to create connection pool: {e}")
            raise e
    return _pool

import time

@contextmanager
def get_db():
    """Context manager for database connections using a pool."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        # Test if connection is still alive, reconnect if needed
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # Connection is stale, close and get a new one
            try:
                conn.close()
            except Exception:
                pass
            pool.putconn(conn, close=True)
            conn = pool.getconn()
        yield conn
    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        # Handle SSL connection issues by closing bad connection
        try:
            conn.close()
        except Exception:
            pass
        pool.putconn(conn, close=True)
        raise e
    finally:
        try:
            pool.putconn(conn)
        except Exception:
            pass


def init_db():
    """Initialize database tables."""
    # Ensure DATABASE_URL is available
    if not DATABASE_URL:
        print("DATABASE_URL not found. Skipping init_db.")
        return

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Candidates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    current_job_title TEXT,
                    current_company TEXT,
                    location TEXT,
                    years_experience INTEGER,
                    skills TEXT,  -- JSON array
                    certifications TEXT,  -- JSON array
                    work_experience TEXT,  -- JSON array of objects
                    education TEXT,  -- JSON array of objects
                    summary TEXT,  -- Professional summary
                    resume_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add new columns if they don't exist (for existing tables)
            # Use savepoints to handle failures without aborting transaction
            new_columns = [
                ("location", "TEXT"),
                ("certifications", "TEXT"),
                ("work_experience", "TEXT"),
                ("education", "TEXT"),
                ("summary", "TEXT"),
            ]
            for col_name, col_type in new_columns:
                try:
                    cursor.execute("SAVEPOINT add_column")
                    cursor.execute(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_type}")
                    cursor.execute("RELEASE SAVEPOINT add_column")
                except Exception:
                    cursor.execute("ROLLBACK TO SAVEPOINT add_column")
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT,
                    description TEXT,
                    requirements TEXT,  -- JSON array
                    preferred_skills TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Calls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY,
                    candidate_id TEXT,
                    job_id TEXT,
                    status TEXT DEFAULT 'pending',
                    conversation_id TEXT,
                    call_sid TEXT,
                    transcript TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)

            # ATS/CRM Connections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ats_connections (
                    user_id TEXT,
                    account_token TEXT NOT NULL,
                    integration TEXT,
                    category TEXT DEFAULT 'ats',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, category)
                )
            """)
            
            conn.commit()


def save_ats_connection(user_id: str, account_token: str, integration: str, category: str = "ats"):
    """Save or update ATS/CRM connection."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ats_connections (user_id, account_token, integration, category)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(user_id, category) DO UPDATE SET
                    account_token=EXCLUDED.account_token,
                    integration=EXCLUDED.integration
            """, (user_id, account_token, integration, category))
        conn.commit()


def get_ats_connection(user_id: str, category: str = "ats") -> Optional[dict]:
    """Get ATS or CRM connection for user."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM ats_connections WHERE user_id = %s AND category = %s", (user_id, category))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "user_id": row["user_id"],
                "account_token": row["account_token"],
                "integration": row["integration"],
                "category": row["category"]
            }


def seed_dummy_data():
    """Seed database with dummy candidates and jobs."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM candidates")
            if cursor.fetchone()[0] > 0:
                print("Database already seeded.")
                return
            
            # Dummy candidates
            candidates = [
                {
                    "id": str(uuid.uuid4()),
                    "full_name": "Sarah Johnson",
                    "email": "sarah.johnson@email.com",
                    "phone": "+13476690154",
                    "current_job_title": "Senior Software Engineer",
                    "current_company": "TechStart Inc",
                    "years_experience": 7,
                    "skills": json.dumps(["Python", "React", "AWS", "Docker", "PostgreSQL", "FastAPI"]),
                    "resume_text": "..."
                },
                {
                    "id": str(uuid.uuid4()),
                    "full_name": "Michael Chen",
                    "email": "m.chen@email.com",
                    "phone": "+14155551234",
                    "current_job_title": "Full Stack Developer",
                    "current_company": "StartupXYZ",
                    "years_experience": 4,
                    "skills": json.dumps(["JavaScript", "TypeScript", "React", "Node.js", "MongoDB", "GraphQL"]),
                    "resume_text": "..."
                },
                {
                    "id": str(uuid.uuid4()),
                    "full_name": "Emily Rodriguez",
                    "email": "emily.r@email.com",
                    "phone": "+12125559876",
                    "current_job_title": "Data Engineer",
                    "current_company": "DataFlow Inc",
                    "years_experience": 5,
                    "skills": json.dumps(["Python", "SQL", "Spark", "Airflow", "AWS", "Snowflake"]),
                    "resume_text": "..."
                }
            ]
            
            # Dummy jobs
            jobs = [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Senior Software Engineer",
                    "company": "Acme Corp",
                    "description": "We're looking for a senior software engineer to lead development of our core platform.",
                    "requirements": json.dumps(["5+ years experience", "Python or Java", "Cloud experience (AWS/GCP)", "Strong system design skills"]),
                    "preferred_skills": json.dumps(["Kubernetes", "PostgreSQL", "React"])
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Full Stack Developer",
                    "company": "TechStart Inc",
                    "description": "Join our fast-growing startup to build next-generation web applications.",
                    "requirements": json.dumps(["3+ years experience", "JavaScript/TypeScript", "React or Vue", "Node.js"]),
                    "preferred_skills": json.dumps(["GraphQL", "MongoDB", "AWS"])
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Data Engineer",
                    "company": "DataDriven LLC",
                    "description": "Build and maintain our data infrastructure to power analytics and ML.",
                    "requirements": json.dumps(["4+ years experience", "Python", "SQL", "ETL pipelines"]),
                    "preferred_skills": json.dumps(["Spark", "Airflow", "Snowflake", "dbt"])
                }
            ]
            
            # Insert candidates
            for c in candidates:
                cursor.execute("""
                    INSERT INTO candidates (id, full_name, email, phone, current_job_title, current_company, years_experience, skills, resume_text)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (c["id"], c["full_name"], c["email"], c["phone"], c["current_job_title"], c["current_company"], c["years_experience"], c["skills"], c["resume_text"]))
            
            # Insert jobs
            for j in jobs:
                cursor.execute("""
                    INSERT INTO jobs (id, title, company, description, requirements, preferred_skills)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (j["id"], j["title"], j["company"], j["description"], j["requirements"], j["preferred_skills"]))
            
            conn.commit()
            print(f"✅ Seeded {len(candidates)} candidates and {len(jobs)} jobs")


def get_all_candidates() -> List[dict]:
    """Get all candidates from database."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            start = time.time()
            cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            # Parse JSON fields
            return [
                {
                    "id": row["id"],
                    "full_name": row["full_name"],
                    "email": row["email"],
                    "phone": row["phone"],
                    "current_job_title": row["current_job_title"],
                    "current_company": row["current_company"],
                    "location": row.get("location"),
                    "years_of_experience": row.get("years_experience"),
                    "skills": json.loads(row["skills"]) if row.get("skills") else [],
                    "certifications": json.loads(row["certifications"]) if row.get("certifications") else [],
                    "work_experience": json.loads(row["work_experience"]) if row.get("work_experience") else [],
                    "education": json.loads(row["education"]) if row.get("education") else [],
                    "summary": row.get("summary"),
                    "resume_text": row["resume_text"]
                }
                for row in rows
            ]


def get_all_jobs() -> List[dict]:
    """Get all jobs from database."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "company": row["company"],
                    "description": row["description"],
                    "requirements": json.loads(row["requirements"]) if row["requirements"] else [],
                    "preferred_skills": json.loads(row["preferred_skills"]) if row["preferred_skills"] else []
                }
                for row in rows
            ]


def get_candidate_by_id(candidate_id: str) -> Optional[dict]:
    """Get candidate by ID."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "full_name": row["full_name"],
                "email": row["email"],
                "phone": row["phone"],
                "current_job_title": row["current_job_title"],
                "current_company": row["current_company"],
                "location": row.get("location"),
                "years_of_experience": row.get("years_experience"),
                "skills": json.loads(row["skills"]) if row.get("skills") else [],
                "certifications": json.loads(row["certifications"]) if row.get("certifications") else [],
                "work_experience": json.loads(row["work_experience"]) if row.get("work_experience") else [],
                "education": json.loads(row["education"]) if row.get("education") else [],
                "summary": row.get("summary"),
                "resume_text": row["resume_text"]
            }


def get_job_by_id(job_id: str) -> Optional[dict]:
    """Get job by ID."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "title": row["title"],
                "company": row["company"],
                "description": row["description"],
                "requirements": json.loads(row["requirements"]) if row["requirements"] else [],
                "preferred_skills": json.loads(row["preferred_skills"]) if row["preferred_skills"] else []
            }


def upsert_candidate(candidate: dict):
    """Insert or update candidate with all fields."""
    # Convert work_experience and education to JSON if they're lists of objects
    work_exp = candidate.get("work_experience", [])
    if work_exp and isinstance(work_exp[0], dict) is False and hasattr(work_exp[0], 'dict'):
        work_exp = [e.dict() if hasattr(e, 'dict') else e for e in work_exp]
    
    education = candidate.get("education", [])
    if education and isinstance(education[0], dict) is False and hasattr(education[0], 'dict'):
        education = [e.dict() if hasattr(e, 'dict') else e for e in education]
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO candidates (
                    id, full_name, email, phone, current_job_title, current_company,
                    location, years_experience, skills, certifications,
                    work_experience, education, summary, resume_text
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(id) DO UPDATE SET
                    full_name=EXCLUDED.full_name,
                    email=EXCLUDED.email,
                    phone=EXCLUDED.phone,
                    current_job_title=EXCLUDED.current_job_title,
                    current_company=EXCLUDED.current_company,
                    location=EXCLUDED.location,
                    years_experience=EXCLUDED.years_experience,
                    skills=EXCLUDED.skills,
                    certifications=EXCLUDED.certifications,
                    work_experience=EXCLUDED.work_experience,
                    education=EXCLUDED.education,
                    summary=EXCLUDED.summary,
                    resume_text=EXCLUDED.resume_text
            """, (
                candidate["id"],
                candidate["full_name"],
                candidate.get("email"),
                candidate.get("phone"),
                candidate.get("current_job_title"),
                candidate.get("current_company"),
                candidate.get("location"),
                candidate.get("years_of_experience") or candidate.get("years_experience", 0),
                json.dumps(candidate.get("skills", [])),
                json.dumps(candidate.get("certifications", [])),
                json.dumps(work_exp),
                json.dumps(education),
                candidate.get("summary"),
                candidate.get("resume_text", "")
            ))
        conn.commit()


def upsert_job(job: dict):
    """Insert or update job."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO jobs (id, title, company, description, requirements, preferred_skills)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT(id) DO UPDATE SET
                    title=EXCLUDED.title,
                    company=EXCLUDED.company,
                    description=EXCLUDED.description,
                    requirements=EXCLUDED.requirements,
                    preferred_skills=EXCLUDED.preferred_skills
            """, (
                job["id"],
                job["title"],
                job.get("company"),
                job.get("description"),
                json.dumps(job.get("requirements", [])),
                json.dumps(job.get("preferred_skills", []))
            ))
        conn.commit()


def upsert_call(call: dict):
    """Insert or update call status."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO calls (id, candidate_id, job_id, status, conversation_id, call_sid, transcript, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    status=EXCLUDED.status,
                    conversation_id=EXCLUDED.conversation_id,
                    call_sid=EXCLUDED.call_sid,
                    transcript=EXCLUDED.transcript
            """, (
                call["call_id"],
                call["candidate_id"],
                call.get("job_id"), # Assuming job_id might be passed or added to schema earlier
                call["status"],
                call.get("conversation_id"),
                call.get("call_sid"),
                call.get("transcript")
            ))
        conn.commit()


def get_call_by_id(call_id: str) -> Optional[dict]:
    """Get call by ID."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM calls WHERE id = %s", (call_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "call_id": row["id"],
                "candidate_id": row["candidate_id"],
                "job_id": row["job_id"],
                "status": row["status"],
                "conversation_id": row["conversation_id"],
                "call_sid": row["call_sid"],
                "transcript": row["transcript"],
                "questions_asked": [], # Not stored in simple schema yet
                "summary": None # Not stored in simple schema yet
            }


def delete_candidate(candidate_id: str) -> bool:
    """Delete a candidate by ID. Returns True if deleted, False if not found."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            # First delete related calls to avoid FK constraint
            cursor.execute("DELETE FROM calls WHERE candidate_id = %s", (candidate_id,))
            cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
            deleted = cursor.rowcount > 0
        conn.commit()
        return deleted


def delete_job(job_id: str) -> bool:
    """Delete a job by ID. Returns True if deleted, False if not found."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            # First delete related calls to avoid FK constraint
            cursor.execute("DELETE FROM calls WHERE job_id = %s", (job_id,))
            cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            deleted = cursor.rowcount > 0
        conn.commit()
        return deleted



if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Seeding dummy data...")
    seed_dummy_data()
    print("Done!")
