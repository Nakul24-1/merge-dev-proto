"""
Merge.dev Integration Service

Handles ATS integration via Merge Unified API.
"""

import os
from typing import Optional, List
import httpx
from pydantic import BaseModel


MERGE_API_URL = "https://api.merge.dev/api"


class ATSCandidate(BaseModel):
    """Candidate from ATS via Merge."""
    id: str
    remote_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    locations: Optional[List[str]] = None


class ATSJob(BaseModel):
    """Job from ATS via Merge."""
    id: str
    remote_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # OPEN, CLOSED, DRAFT, etc.
    departments: Optional[List[str]] = None


def get_api_key() -> str:
    """Get Merge API key from environment."""
    key = os.getenv("MERGE_API_KEY")
    if not key:
        raise ValueError("MERGE_API_KEY not set in environment")
    return key


async def create_link_token(
    end_user_origin_id: str,
    end_user_organization_name: str,
    end_user_email: str,
    categories: List[str] = None
) -> dict:
    """
    Create a link token to initialize Merge Link for an end user.
    
    Returns:
        dict with link_token and optional magic_link_url
    """
    api_key = get_api_key()
    
    payload = {
        "end_user_origin_id": end_user_origin_id,
        "end_user_organization_name": end_user_organization_name,
        "end_user_email_address": end_user_email,
        "categories": categories or ["ats"]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERGE_API_URL}/integrations/create-link-token",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to create link token: {response.status_code} - {response.text}")


async def exchange_public_token(public_token: str) -> dict:
    """
    Exchange a public token from Merge Link for an account token.
    
    Returns:
        dict with account_token and account details
    
    Note: Category is determined from integration.categories in the API response,
    not by which endpoint succeeds (fixes HubSpot CRM marking ATS as connected).
    """
    api_key = get_api_key()
    
    async with httpx.AsyncClient() as client:
        # Try ATS endpoint first (primary use case for recruitment app)
        response = await client.get(
            f"{MERGE_API_URL}/ats/v1/account-token/{public_token}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            # Get category from integration.categories (authoritative source per Merge docs)
            integration = data.get("integration", {})
            categories = integration.get("categories", [])
            # Use first category, default to "ats" since we hit ATS endpoint
            data["category"] = categories[0].lower() if categories else "ats"
            return data
            
        # Fallback to CRM endpoint if ATS didn't work
        response = await client.get(
            f"{MERGE_API_URL}/crm/v1/account-token/{public_token}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            # Get category from integration.categories (authoritative source)
            integration = data.get("integration", {})
            categories = integration.get("categories", [])
            data["category"] = categories[0].lower() if categories else "crm"
            return data
        else:
            raise Exception(f"Failed to exchange token: {response.status_code} - {response.text}")


# ... (get_candidates, get_jobs code remains same, omitted for brevity in tool call)


async def create_crm_contact(account_token: str, contact_data: dict) -> dict:
    """
    Create a contact in the connected CRM.
    
    Args:
        account_token: The CRM account token
        contact_data: Dict containing first_name, last_name, email, phone_numbers, description
    """
    api_key = get_api_key()
    
    # Map to Merge CRM Contact model
    # Note: Merge API uses "email_address" and "phone_number" as field names, not "value"
    payload = {
        "model": {
            "first_name": contact_data.get("first_name"),
            "last_name": contact_data.get("last_name"),
            "title": contact_data.get("title"),
            "email_addresses": [{"email_address": contact_data.get("email"), "email_address_type": "WORK"}] if contact_data.get("email") else [],
            "phone_numbers": [{"phone_number": contact_data.get("phone"), "phone_number_type": "WORK"}] if contact_data.get("phone") else [],
            "description": f"{contact_data.get('description', '')}\n\nCurrent Company: {contact_data.get('company', 'Unknown')}"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERGE_API_URL}/crm/v1/contacts",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Account-Token": account_token,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create CRM contact: {response.status_code} - {response.text}")


async def get_candidates(account_token: str, page_size: int = 50) -> List[ATSCandidate]:
    """
    Fetch candidates from the connected ATS.
    """
    api_key = get_api_key()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MERGE_API_URL}/ats/v1/candidates",
            params={"page_size": page_size},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Account-Token": account_token
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            candidates = []
            for item in data.get("results", []):
                # Extract first email and phone
                emails = item.get("email_addresses", [])
                phones = item.get("phone_numbers", [])
                email = emails[0].get("value") if emails else None
                phone = phones[0].get("value") if phones else None
                
                candidates.append(ATSCandidate(
                    id=item.get("id"),
                    remote_id=item.get("remote_id"),
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                    company=item.get("company"),
                    title=item.get("title"),
                    email=email,
                    phone=phone,
                    locations=item.get("locations", []),
                    tags=item.get("tags", [])
                ))
            return candidates
        else:
            raise Exception(f"Failed to fetch candidates: {response.status_code} - {response.text}")


async def get_jobs(account_token: str, page_size: int = 50) -> List[ATSJob]:
    """
    Fetch jobs from the connected ATS.
    """
    api_key = get_api_key()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MERGE_API_URL}/ats/v1/jobs",
            params={"page_size": page_size},
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Account-Token": account_token
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for item in data.get("results", []):
                jobs.append(ATSJob(
                    id=item.get("id"),
                    remote_id=item.get("remote_id"),
                    name=item.get("name"),
                    description=item.get("description"),
                    status=item.get("status"),
                    departments=item.get("departments", [])
                ))
            return jobs
        else:
            raise Exception(f"Failed to fetch jobs: {response.status_code} - {response.text}")


async def get_linked_accounts(category: str = None) -> List[dict]:
    """
    Get list of linked accounts (connected integrations).
    
    Args:
        category: Optional filter - 'ats', 'crm', or None for both
    """
    api_key = get_api_key()
    all_accounts = []
    
    async with httpx.AsyncClient() as client:
        # Fetch ATS accounts if no category filter or category is 'ats'
        if category is None or category == "ats":
            response = await client.get(
                f"{MERGE_API_URL}/ats/v1/linked-accounts",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0
            )
            if response.status_code == 200:
                ats_accounts = response.json().get("results", [])
                for acc in ats_accounts:
                    acc["_category"] = "ats"
                all_accounts.extend(ats_accounts)
        
        # Fetch CRM accounts if no category filter or category is 'crm'
        if category is None or category == "crm":
            response = await client.get(
                f"{MERGE_API_URL}/crm/v1/linked-accounts",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0
            )
            if response.status_code == 200:
                crm_accounts = response.json().get("results", [])
                for acc in crm_accounts:
                    acc["_category"] = "crm"
                all_accounts.extend(crm_accounts)
    
    return all_accounts


async def sync_user_connections(user_id: str) -> dict:
    """
    Sync connections from Merge API to local DB for a user.
    
    This ensures the local DB is in sync with what's actually connected in Merge.
    Should be called after connecting via Merge Link or when checking status.
    
    Note: account_token is only available for connections made through our app.
    For connections made directly in Merge dashboard, we can only see they exist.
    
    Returns:
        dict with synced connection counts and status
    """
    from app.db.database import save_ats_connection
    
    linked_accounts = await get_linked_accounts()
    
    synced = {"ats": 0, "crm": 0, "accounts_found": len(linked_accounts), "user_accounts": [], "missing_tokens": []}
    
    for account in linked_accounts:
        # Match by end_user_origin_id (which we set to user_id during link token creation)
        if account.get("end_user_origin_id") == user_id:
            category = account.get("_category", "ats")
            
            # Integration may be a dict with 'name' key or a string
            integration_data = account.get("integration")
            if isinstance(integration_data, dict):
                integration_name = integration_data.get("name", "Unknown")
            else:
                integration_name = str(integration_data) if integration_data else "Unknown"
            
            account_token = account.get("account_token")
            
            synced["user_accounts"].append({
                "integration": integration_name,
                "category": category,
                "has_token": bool(account_token)
            })
            
            if account_token:
                save_ats_connection(
                    user_id=user_id,
                    account_token=account_token,
                    integration=integration_name,
                    category=category
                )
                synced[category] += 1
            else:
                # Account exists but token not available (connected via different flow)
                synced["missing_tokens"].append(integration_name)
    
    return synced

