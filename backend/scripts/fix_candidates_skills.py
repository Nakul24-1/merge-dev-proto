import sqlite3
import json
from pathlib import Path

DB_PATH = Path("app/data/screening.db")

def fix_skills_data():
    print(f"Checking database at {DB_PATH.absolute()}")
    conn = sqlite3.connect(str(DB_PATH))
    # Enable accessing columns by name
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, skills FROM candidates")
        rows = cursor.fetchall()
        
        for row in rows:
            candidate_id = row['id']
            skills_raw = row['skills']
            
            if not skills_raw:
                continue
                
            try:
                # Try parsing as JSON
                json.loads(skills_raw)
                # If successful, it's valid JSON, presumably (could be just a valid string "foo", but we want list)
                # We can verify if it's a list if we want, but mainly we want to fix crashers.
                # print(f"Candidate {candidate_id}: Valid JSON")
                pass
            except json.JSONDecodeError:
                print(f"Candidate {candidate_id}: Bad JSON detected -> '{skills_raw}'")
                
                # Assume it's comma separated string from my manual bad update
                # e.g. "Python, React, AWS"
                if ',' in skills_raw:
                    new_skills_list = [s.strip() for s in skills_raw.split(',')]
                else:
                    new_skills_list = [skills_raw.strip()]
                
                new_skills_json = json.dumps(new_skills_list)
                print(f"  -> Converting to: {new_skills_json}")
                
                cursor.execute("UPDATE candidates SET skills = ? WHERE id = ?", (new_skills_json, candidate_id))
        
        conn.commit()
        print("✅ Database repair complete.")
        
    except Exception as e:
        print(f"❌ Error during repair: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_skills_data()
