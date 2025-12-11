import sqlite3
from pathlib import Path

DB_PATH = Path("app/data/screening.db")

def populate_candidate():
    print(f"Updating candidate in {DB_PATH}...")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Update the first candidate to have rich data
    # We assume 'candidates' table exists and has these columns
    # Note: 'current_job_title' might not exist in schema if it wasn't added purely for this proto.
    # Let's check schema first or use JSON blob if that's how it's stored?
    # Based on database.py: upsert_candidate uses:
    # id, first_name, last_name, email, phone, current_job_title, years_experience, skills, resume_text
    
    try:
        cursor.execute("SELECT id FROM candidates LIMIT 1")
        row = cursor.fetchone()
        if not row:
            print("No candidates found.")
            return

        candidate_id = row[0]
        print(f"Updating Candidate {candidate_id}")
        
        cursor.execute("""
            UPDATE candidates 
            SET 
                email = 'test.user@example.com',
                phone = '+15550001234',
                current_job_title = 'Senior Python Engineer',
                years_experience = 7,
                skills = 'Python, React, AWS'
            WHERE id = ?
        """, (candidate_id,))
        
        conn.commit()
        print("✅ Candidate updated with test data.")
        
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    populate_candidate()
