import sqlite3
import json
from pathlib import Path

DB_PATH = Path("app/data/screening.db")

def inspect_candidates():
    print(f"--- Inspecting Candidates in {DB_PATH} ---")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, full_name, email, phone, current_company, current_job_title FROM candidates")
        rows = cursor.fetchall()
        
        for row in rows:
            print("-" * 40)
            print(f"Name: {row['full_name']}")
            print(f"ID:   {row['id']}")
            print(f"Email: {row['email']}")
            print(f"Phone: {row['phone']}")
            print(f"Company: {row['current_company']}")
            print(f"Title:   {row['current_job_title']}")
            
        if not rows:
            print("No candidates found.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_candidates()
