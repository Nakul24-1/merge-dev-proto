import sqlite3
import json
from pathlib import Path

DB_PATH = Path("app/data/screening.db")

def backfill_data():
    print(f"Backfilling data in {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    updates = {
        "Sarah Johnson": {
            "email": "sarah.johnson@example.com",
            "phone": "+15551234567",
            "company": "TechStart Inc",
            "title": "Senior Software Engineer"
        },
        "Michael Chen": {
            "email": "michael.chen@example.com",
            "phone": "+15559876543",
            "company": "StartupXYZ",
            "title": "Full Stack Developer"
        },
        "Emily Rodriguez": {
            "email": "emily.rodriguez@example.com",
            "phone": "+15551112222",
            "company": "DataFlow Inc",
            "title": "Data Engineer"
        }
    }
    
    try:
        cursor.execute("SELECT id, full_name, email, phone, current_company FROM candidates")
        rows = cursor.fetchall()
        
        for row in rows:
            name = row["full_name"]
            if name in updates:
                data = updates[name]
                print(f"Updating {name}...")
                
                # Check if we need to update company (new column) or empty phone/email
                # We overwrite to be safe
                cursor.execute("""
                    UPDATE candidates 
                    SET email = ?, phone = ?, current_company = ?, current_job_title = ?
                    WHERE id = ?
                """, (data["email"], data["phone"], data["company"], data["title"], row["id"]))
                
        conn.commit()
        print("✅ Backfill complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    backfill_data()
