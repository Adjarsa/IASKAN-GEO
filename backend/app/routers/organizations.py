"""
Organization Router
API endpoints for organization/workspace management
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
import uuid

from ..core.database import db
from ..models.organization import Organization, OrganizationMember, OrganizationInvite

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])


# Request/Response Models
class OrganizationCreate(BaseModel):
    name: str
    website_url: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None


class InviteMember(BaseModel):
    email: EmailStr
    role: str = "member"


class AcceptInvite(BaseModel):
    token: str


# Helper to get current user (imported from main server)
async def get_current_user(request: Request) -> dict:
    """Get current user - will be replaced with proper dependency"""
    from ..core.database import db
    
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Session expirée")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return user


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name"""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return f"{slug}-{uuid.uuid4().hex[:6]}"


@router.post("")
async def create_organization(data: OrganizationCreate, user: dict = Depends(get_current_user)):
    """Create a new organization"""
    # Check if user already owns an organization
    existing = await db.organizations.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà une organisation")
    
    org = Organization(
        name=data.name,
        slug=generate_slug(data.name),
        owner_id=user["user_id"],
        website_url=data.website_url,
        industry=data.industry,
        size=data.size,
        members=[OrganizationMember(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            role="owner"
        )]
    )
    
    doc = org.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["members"][0]["joined_at"] = doc["members"][0]["joined_at"].isoformat()
    
    await db.organizations.insert_one(doc)
    
    # Update user's organization_id
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"organization_id": org.organization_id}}
    )
    
    # Return without _id
    result = await db.organizations.find_one(
        {"organization_id": org.organization_id},
        {"_id": 0}
    )
    
    return {"organization": result}


@router.get("")
async def get_user_organizations(user: dict = Depends(get_current_user)):
    """Get organizations the user belongs to"""
    orgs = await db.organizations.find(
        {"members.user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(100)
    
    return {"organizations": orgs}


@router.get("/{org_id}")
async def get_organization(org_id: str, user: dict = Depends(get_current_user)):
    """Get organization details"""
    org = await db.organizations.find_one(
        {"organization_id": org_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    return {"organization": org}


@router.put("/{org_id}")
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    user: dict = Depends(get_current_user)
):
    """Update organization (owner/admin only)"""
    org = await db.organizations.find_one(
        {"organization_id": org_id},
        {"_id": 0}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    # Check permission
    member = next((m for m in org.get("members", []) if m["user_id"] == user["user_id"]), None)
    if not member or member["role"] not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Permission insuffisante")
    
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.organizations.update_one(
            {"organization_id": org_id},
            {"$set": updates}
        )
    
    updated = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    return {"organization": updated}


@router.delete("/{org_id}")
async def delete_organization(org_id: str, user: dict = Depends(get_current_user)):
    """Delete organization (owner only)"""
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    if org.get("owner_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut supprimer l'organisation")
    
    # Remove organization_id from all members
    for member in org.get("members", []):
        await db.users.update_one(
            {"user_id": member["user_id"]},
            {"$unset": {"organization_id": ""}}
        )
    
    await db.organizations.delete_one({"organization_id": org_id})
    
    return {"message": "Organisation supprimée"}


@router.post("/{org_id}/invite")
async def invite_member(
    org_id: str,
    data: InviteMember,
    user: dict = Depends(get_current_user)
):
    """Invite a new member to the organization"""
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    # Check permission
    member = next((m for m in org.get("members", []) if m["user_id"] == user["user_id"]), None)
    if not member or member["role"] not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Permission insuffisante")
    
    # Check if already a member
    existing_member = next((m for m in org.get("members", []) if m["email"] == data.email), None)
    if existing_member:
        raise HTTPException(status_code=400, detail="Cet utilisateur est déjà membre")
    
    # Create invitation
    invite = OrganizationInvite(
        organization_id=org_id,
        email=data.email,
        role=data.role,
        invited_by=user["user_id"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    
    doc = invite.model_dump()
    doc["expires_at"] = doc["expires_at"].isoformat()
    doc["created_at"] = doc["created_at"].isoformat()
    
    await db.organization_invites.insert_one(doc)
    
    # TODO: Send invitation email
    
    return {
        "success": True,
        "message": f"Invitation envoyée à {data.email}",
        "invite_token": invite.token
    }


@router.post("/invites/accept")
async def accept_invite(data: AcceptInvite, user: dict = Depends(get_current_user)):
    """Accept an organization invitation"""
    invite = await db.organization_invites.find_one(
        {"token": data.token, "accepted": False},
        {"_id": 0}
    )
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation invalide ou expirée")
    
    # Check expiration
    expires_at = datetime.fromisoformat(invite["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Cette invitation a expiré")
    
    # Check email match
    if invite["email"] != user["email"]:
        raise HTTPException(status_code=403, detail="Cette invitation n'est pas pour vous")
    
    # Add member to organization
    new_member = {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "role": invite["role"],
        "invited_by": invite["invited_by"],
        "joined_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.organizations.update_one(
        {"organization_id": invite["organization_id"]},
        {"$push": {"members": new_member}}
    )
    
    # Update user's organization_id
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"organization_id": invite["organization_id"]}}
    )
    
    # Mark invite as accepted
    await db.organization_invites.update_one(
        {"token": data.token},
        {"$set": {"accepted": True}}
    )
    
    return {"success": True, "message": "Vous avez rejoint l'organisation"}


@router.delete("/{org_id}/members/{member_user_id}")
async def remove_member(
    org_id: str,
    member_user_id: str,
    user: dict = Depends(get_current_user)
):
    """Remove a member from the organization"""
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    # Check permission (owner/admin or self-removal)
    current_member = next((m for m in org.get("members", []) if m["user_id"] == user["user_id"]), None)
    is_self_removal = member_user_id == user["user_id"]
    
    if not current_member:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas membre de cette organisation")
    
    if not is_self_removal and current_member["role"] not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Permission insuffisante")
    
    # Cannot remove owner
    if member_user_id == org.get("owner_id"):
        raise HTTPException(status_code=400, detail="Impossible de retirer le propriétaire")
    
    # Remove member
    await db.organizations.update_one(
        {"organization_id": org_id},
        {"$pull": {"members": {"user_id": member_user_id}}}
    )
    
    # Update user's organization_id
    await db.users.update_one(
        {"user_id": member_user_id},
        {"$unset": {"organization_id": ""}}
    )
    
    return {"success": True, "message": "Membre retiré"}


@router.put("/{org_id}/members/{member_user_id}/role")
async def update_member_role(
    org_id: str,
    member_user_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Update a member's role"""
    body = await request.json()
    new_role = body.get("role", "member")
    
    if new_role not in ["admin", "member", "viewer"]:
        raise HTTPException(status_code=400, detail="Rôle invalide")
    
    org = await db.organizations.find_one({"organization_id": org_id}, {"_id": 0})
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    # Only owner can change roles
    if org.get("owner_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut modifier les rôles")
    
    # Cannot change owner's role
    if member_user_id == org.get("owner_id"):
        raise HTTPException(status_code=400, detail="Impossible de modifier le rôle du propriétaire")
    
    # Update role
    await db.organizations.update_one(
        {"organization_id": org_id, "members.user_id": member_user_id},
        {"$set": {"members.$.role": new_role}}
    )
    
    return {"success": True, "message": f"Rôle mis à jour: {new_role}"}
