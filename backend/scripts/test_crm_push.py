import asyncio
import httpx
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Config
BASE_URL = "http://127.0.0.1:8000/api/v1"
USER_ID = "user_123"

def get_first_candidate_id():
    if not DATABASE_URL:
        print("DATABASE_URL not set")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM candidates LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        print(f"DB Error: {e}")
    return None

async def test_push_contact():
    print(f"Testing CRM Push for User: {USER_ID}")
    
    # 1. Get a candidate ID
    candidate_id = get_first_candidate_id()
    if not candidate_id:
        print("❌ No candidates found in DB. Cannot test.")
        return

    print(f"Using Candidate ID: {candidate_id}")

    # 2. Call Push Endpoint
    url = f"{BASE_URL}/merge/crm/push-candidate"
    payload = {
        "user_id": USER_ID,
        "candidate_id": candidate_id,
        "description_override": "[TEST] Automated CRM Push Test"
    }
    
    print(f"POST {url}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            
            if response.status_code == 200:
                print("✅ Success!")
                print("Response:", response.json())
            else:
                print(f"❌ Failed: {response.status_code}")
                print("Response:", response.text)
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_push_contact())
