import sqlite3
from pathlib import Path

DB_PATH = Path("app/data/screening.db")

def add_company_column():
    print(f"Migrating database at {DB_PATH.absolute()}")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(candidates)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "current_company" in columns:
            print("Column 'current_company' already exists.")
        else:
            print("Adding 'current_company' column...")
            cursor.execute("ALTER TABLE candidates ADD COLUMN current_company TEXT")
            conn.commit()
            print("✅ Column added successfully.")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_company_column()
