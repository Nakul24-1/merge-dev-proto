import sqlite3
from pathlib import Path

DB_PATH = Path("app/data/screening.db")

def fix_hubspot():
    print(f"Opening database at {DB_PATH.absolute()}")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Find the HubSpot connection
        cursor.execute("SELECT user_id, integration, category FROM ats_connections WHERE integration LIKE '%HubSpot%'")
        rows = cursor.fetchall()
        print(f"Found connections: {rows}")
        
        if not rows:
            print("No HubSpot connection found!")
            return

        for row in rows:
            user_id, integration, category = row
            if category == 'ats':
                print(f"Updating {integration} for {user_id} from 'ats' to 'crm'...")
                try:
                    cursor.execute("""
                        UPDATE ats_connections 
                        SET category = 'crm' 
                        WHERE user_id = ? AND integration = ? AND category = 'ats'
                    """, (user_id, integration))
                    print("Update executed.")
                except sqlite3.IntegrityError as e:
                    print(f"Update failed (maybe 'crm' entries already exist?): {e}")
            else:
                print(f"{integration} is already category '{category}'")

        conn.commit()
        print("✅ Database update complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_hubspot()
