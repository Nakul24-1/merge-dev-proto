"""
Merge.dev API Endpoints

Handles ATS connection flow and data sync.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.merge_service import (
    create_link_token,
    exchange_public_token,
    get_candidates,
    get_jobs,
    get_linked_accounts,
    create_crm_contact,
    sync_user_connections,
    ATSCandidate,
    ATSJob
)

from app.db.database import (
    save_ats_connection, 
    get_ats_connection,
    upsert_candidate,
    upsert_job
)

router = APIRouter(prefix="/merge", tags=["Merge ATS Integration"])


class SyncResponse(BaseModel):
    candidates_synced: int
    jobs_synced: int
    message: str

# ... (LinkTokenRequest/Response, TokenExchangeRequest/Response, LinkedAccount models remain same) ...

@router.post("/sync/{user_id}", response_model=SyncResponse)
async def sync_data(user_id: str):
    """
    Sync candidates and jobs from ATS to local database.
    """
    connection = get_ats_connection(user_id)
    if not connection:
        raise HTTPException(status_code=400, detail="No ATS connected. Connect first.")
    
    try:
        # 1. Fetch from ATS
        ats_candidates = await get_candidates(connection["account_token"])
        ats_jobs = await get_jobs(connection["account_token"])
        
        # 2. Upsert Candidates
        for c in ats_candidates:
            candidate_dict = {
                "id": c.id,  # Use Merge ID as local ID
                "full_name": f"{c.first_name} {c.last_name}".strip(),
                "email": c.email,
                "phone": c.phone,
                "current_job_title": c.title,
                "years_experience": 0, # Not provided by std candidate model usually
                "skills": c.tags or [], # Map tags to skills
                "resume_text": ""      # Would need to fetch attachment content
            }
            upsert_candidate(candidate_dict)
            
        # 3. Upsert Jobs
        for j in ats_jobs:
            job_dict = {
                "id": j.id,
                "title": j.name,
                "company": "Synced ATS Company", # Often not in job model directly, implies org
                "description": j.description,
                "requirements": [],
                "preferred_skills": []
            }
            upsert_job(job_dict)
            
        return SyncResponse(
            candidates_synced=len(ats_candidates),
            jobs_synced=len(ats_jobs),
            message="Sync completed successfully"
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



class LinkTokenRequest(BaseModel):
    user_id: str
    organization_name: str
    email: str
    categories: Optional[List[str]] = ["ats", "crm"]  # Default to both


class LinkTokenResponse(BaseModel):
    link_token: str
    magic_link_url: Optional[str] = None


class TokenExchangeRequest(BaseModel):
    user_id: str
    public_token: str


class TokenExchangeResponse(BaseModel):
    success: bool
    account_token: Optional[str] = None
    integration: Optional[str] = None
    message: str


class LinkedAccount(BaseModel):
    id: str
    integration: str
    status: str
    end_user_origin_id: Optional[str] = None


@router.post("/link-token", response_model=LinkTokenResponse)
async def create_merge_link_token(request: LinkTokenRequest):
    """
    Create a link token to initialize Merge Link for the user.
    
    The frontend uses this token to open the Merge Link UI.
    """
    try:
        result = await create_link_token(
            end_user_origin_id=request.user_id,
            end_user_organization_name=request.organization_name,
            end_user_email=request.email,
            categories=request.categories
        )
        return LinkTokenResponse(
            link_token=result.get("link_token"),
            magic_link_url=result.get("magic_link_url")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect", response_model=TokenExchangeResponse)
async def connect_ats(request: TokenExchangeRequest):
    """
    Exchange the public token from Merge Link for an account token.
    
    Called after the user successfully connects their ATS via Merge Link.
    """
    try:
        result = await exchange_public_token(request.public_token)
        account_token = result.get("account_token")
        
        # Integration comes back as a dict from Merge API
        integration_data = result.get("integration")
        integration_name = integration_data.get("name") if isinstance(integration_data, dict) else str(integration_data)
        
        category = result.get("category", "ats") # Merge returns category
        
        # Store the account token in DB with category
        save_ats_connection(request.user_id, account_token, integration_name, category=category)
        
        return TokenExchangeResponse(
            success=True,
            account_token=account_token,
            integration=integration_name,
            message=f"Successfully connected to {integration_name} ({category})"
        )
    except Exception as e:
        return TokenExchangeResponse(
            success=False,
            message=str(e)
        )

class PushContactRequest(BaseModel):
    user_id: str
    candidate_id: str
    description_override: Optional[str] = None

@router.post("/crm/push-candidate", response_model=dict)
async def push_candidate_to_crm(request: PushContactRequest):
    """
    Push a candidate to the connected CRM as a Contact.
    """
    # 1. Get CRM Connection
    connection = get_ats_connection(request.user_id, category="crm")
    if not connection:
        raise HTTPException(status_code=400, detail="No CRM connected. Connect a CRM first.")

    # 2. Get Candidate Data
    # Import here to avoid circular dependencies if possible, or assume db/schema available
    from app.db.database import get_candidate_by_id
    candidate = get_candidate_by_id(request.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    try:
        # 3. Create Contact in CRM
        contact_data = {
            "first_name": candidate["full_name"].split(" ")[0],
            "last_name": " ".join(candidate["full_name"].split(" ")[1:]) if " " in candidate["full_name"] else "",
            "title": candidate.get("current_job_title", ""),
            "company": candidate.get("current_company", ""),
            "email": candidate["email"],
            "phone": candidate["phone"],
            "description": request.description_override or f"AI Screened Candidate. Skills: {candidate.get('skills', 'N/A')}. Location: {candidate.get('location', 'N/A')}"
        }
        
        result = await create_crm_contact(connection["account_token"], contact_data)
        
        return {
            "success": True,
            "crm_contact_id": result.get("model", {}).get("id"),
            "message": "Candidate pushed to CRM successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linked-accounts", response_model=List[LinkedAccount])
async def list_linked_accounts():
    """
    Get all linked ATS and CRM accounts.
    """
    try:
        accounts = await get_linked_accounts()
        result = []
        for acc in accounts:
            # Integration may be a dict with 'name' key or a string
            integration_data = acc.get("integration")
            if isinstance(integration_data, dict):
                integration_name = integration_data.get("name", "Unknown")
            else:
                integration_name = str(integration_data) if integration_data else "Unknown"
            
            result.append(LinkedAccount(
                id=acc.get("id", ""),
                integration=integration_name,
                status=acc.get("status", "COMPLETE"),
                end_user_origin_id=acc.get("end_user_origin_id")
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linked-accounts-debug")
async def list_linked_accounts_debug():
    """
    Debug: Get raw linked accounts data from Merge API.
    """
    try:
        accounts = await get_linked_accounts()
        return {"accounts": accounts, "count": len(accounts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates/{user_id}", response_model=List[ATSCandidate])
async def fetch_candidates(user_id: str):
    """
    Fetch candidates from the user's connected ATS.
    """
    connection = get_ats_connection(user_id)
    if not connection:
        raise HTTPException(status_code=400, detail="No ATS connected for this user. Use /merge/link-token first.")
    
    try:
        candidates = await get_candidates(connection["account_token"])
        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{user_id}", response_model=List[ATSJob])
async def fetch_jobs(user_id: str):
    """
    Fetch jobs from the user's connected ATS.
    """
    connection = get_ats_connection(user_id)
    if not connection:
        raise HTTPException(status_code=400, detail="No ATS connected for this user. Use /merge/link-token first.")
    
    try:
        jobs = await get_jobs(connection["account_token"])
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{user_id}")
async def get_connection_status(user_id: str):
    """
    Check if a user has connected ATS and/or CRM.
    
    Combines local DB data (for tokens) with Merge API data (for real status).
    Uses the integration's actual categories to prevent misclassification.
    """
    # Check local DB (has tokens for API calls)
    ats_connection = get_ats_connection(user_id, category="ats")
    crm_connection = get_ats_connection(user_id, category="crm")
    
    # Also check Merge API directly for full picture
    merge_ats = set()  # Use sets to avoid duplicates
    merge_crm = set()
    try:
        linked_accounts = await get_linked_accounts()
        for acc in linked_accounts:
            if acc.get("end_user_origin_id") == user_id:
                integration_data = acc.get("integration", {})
                integration_name = integration_data.get("name") if isinstance(integration_data, dict) else str(integration_data)
                
                # Use the integration's actual categories (authoritative source)
                # instead of just trusting _category from which endpoint returned it
                if isinstance(integration_data, dict):
                    categories = [c.lower() for c in integration_data.get("categories", [])]
                else:
                    categories = [acc.get("_category", "ats")]
                
                # Add to appropriate sets based on integration's reported categories
                if "ats" in categories:
                    merge_ats.add(integration_name)
                if "crm" in categories:
                    merge_crm.add(integration_name)
    except Exception:
        pass  # If API fails, fall back to local DB only
    
    # Convert sets to lists for JSON response
    merge_ats_list = list(merge_ats)
    merge_crm_list = list(merge_crm)
    
    return {
        "connected": bool(ats_connection) or bool(crm_connection) or bool(merge_ats) or bool(merge_crm),
        "ats_connected": bool(ats_connection) or bool(merge_ats),
        "crm_connected": bool(crm_connection) or bool(merge_crm),
        "user_id": user_id,
        "ats_integration": ats_connection["integration"] if ats_connection else (merge_ats_list[0] if merge_ats_list else None),
        "crm_integration": crm_connection["integration"] if crm_connection else (merge_crm_list[0] if merge_crm_list else None),
        "has_ats_token": bool(ats_connection),
        "has_crm_token": bool(crm_connection),
        "merge_ats": merge_ats_list,
        "merge_crm": merge_crm_list
    }


@router.post("/sync-connections/{user_id}")
async def sync_connections(user_id: str):
    """
    Sync connections from Merge API to local DB.
    
    Call this after connecting via Merge Link to ensure local DB is in sync.
    Also useful to fix out-of-sync issues.
    """
    try:
        synced = await sync_user_connections(user_id)
        return {
            "success": True,
            "synced": synced,
            "message": f"Synced {synced['ats']} ATS and {synced['crm']} CRM connections"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
