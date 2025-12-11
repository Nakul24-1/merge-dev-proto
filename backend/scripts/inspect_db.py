import sqlite3
from pathlib import Path

DB_PATH = Path("app/data/screening.db")

def check_db():
    print(f"Checking database at {DB_PATH.absolute()}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n--- ATS Connections ---")
    try:
        cursor.execute("SELECT user_id, integration, category, created_at FROM ats_connections")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
        if not rows:
            print("No connections found.")
    except Exception as e:
        print(f"Error reading ats_connections: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_db()
