import sqlite3
import os
from pathlib import Path

# Path relative to backend/ directory
DB_PATH = Path("app/data/screening.db")

def migrate():
    print(f"Checking database at {DB_PATH.absolute()}")
    
    if not DB_PATH.exists():
        print("Database not found!")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check current schema
        print("Checking current schema...")
        cursor.execute("PRAGMA table_info(ats_connections)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col}")

        # Start migration
        conn.execute("BEGIN TRANSACTION")
        
        # 1. Rename existing table
        print("Renaming old table...")
        # Check if ats_connections_old already exists (cleanup from failed run)
        cursor.execute("DROP TABLE IF EXISTS ats_connections_old")
        cursor.execute("ALTER TABLE ats_connections RENAME TO ats_connections_old")
        
        # 2. Create new table with correct Primary Key
        print("Creating new table...")
        cursor.execute("""
            CREATE TABLE ats_connections (
                user_id TEXT,
                account_token TEXT NOT NULL,
                integration TEXT,
                category TEXT DEFAULT 'ats',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, category)
            )
        """)
        
        # 3. Copy data
        print("Copying data...")
        # Check if 'category' column existed in old table
        has_category = any(col[1] == 'category' for col in columns)
        
        if has_category:
            cursor.execute("""
                INSERT INTO ats_connections (user_id, account_token, integration, category, created_at)
                SELECT user_id, account_token, integration, category, created_at FROM ats_connections_old
            """)
        else:
            # If migration happened partially or not at all, handle gracefull
            cursor.execute("""
                INSERT INTO ats_connections (user_id, account_token, integration, category, created_at)
                SELECT user_id, account_token, integration, 'ats', created_at FROM ats_connections_old
            """)
            
        # 4. Drop old table
        print("Dropping old table...")
        cursor.execute("DROP TABLE ats_connections_old")
        
        conn.commit()
        print("✅ Migration successful: Primary Key updated to (user_id, category)")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
