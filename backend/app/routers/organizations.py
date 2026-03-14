"""
Organization Router - PostgreSQL Version
API endpoints for organization/workspace management
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update, delete
import uuid

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


async def get_current_user(request: Request) -> dict:
    """Get current user - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import UserSession, User
    
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    async with async_session_maker() as session:
        # Find session
        result = await session.execute(
            select(UserSession).where(UserSession.session_token == token)
        )
        user_session = result.scalar_one_or_none()
        
        if not user_session:
            raise HTTPException(status_code=401, detail="Session expirée")
        
        # Find user
        result = await session.execute(
            select(User).where(User.user_id == user_session.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "plan": user.plan
        }


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name"""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return f"{slug}-{uuid.uuid4().hex[:6]}"


@router.get("")
async def list_organizations(user: dict = Depends(get_current_user)):
    """List organizations for current user - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import Organization, OrganizationMember
    
    async with async_session_maker() as session:
        # Find organizations where user is a member
        result = await session.execute(
            select(Organization)
            .join(OrganizationMember, Organization.org_id == OrganizationMember.org_id)
            .where(OrganizationMember.user_id == user["user_id"])
        )
        orgs = result.scalars().all()
        
        return {
            "organizations": [
                {
                    "org_id": org.org_id,
                    "name": org.name,
                    "slug": org.slug,
                    "owner_id": org.owner_id,
                    "website_url": org.website_url,
                    "industry": org.industry,
                    "logo_url": org.logo_url,
                    "created_at": org.created_at.isoformat() if org.created_at else None
                }
                for org in orgs
            ]
        }


@router.post("")
async def create_organization(data: OrganizationCreate, user: dict = Depends(get_current_user)):
    """Create a new organization - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import Organization, OrganizationMember
    
    async with async_session_maker() as session:
        # Check if user already owns an organization
        result = await session.execute(
            select(Organization).where(Organization.owner_id == user["user_id"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Vous avez déjà une organisation")
        
        # Create organization
        org_id = f"org_{uuid.uuid4().hex[:12]}"
        org = Organization(
            org_id=org_id,
            name=data.name,
            slug=generate_slug(data.name),
            owner_id=user["user_id"],
            website_url=data.website_url,
            industry=data.industry
        )
        session.add(org)
        
        # Add owner as member
        member = OrganizationMember(
            member_id=f"mem_{uuid.uuid4().hex[:12]}",
            org_id=org_id,
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            role="owner"
        )
        session.add(member)
        
        await session.commit()
        
        return {
            "organization": {
                "org_id": org_id,
                "name": data.name,
                "slug": org.slug,
                "owner_id": user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }


@router.get("/{org_id}")
async def get_organization(org_id: str, user: dict = Depends(get_current_user)):
    """Get organization details - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import Organization, OrganizationMember
    
    async with async_session_maker() as session:
        # Check membership
        result = await session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
            .where(OrganizationMember.user_id == user["user_id"])
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Get organization
        result = await session.execute(
            select(Organization).where(Organization.org_id == org_id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organisation non trouvée")
        
        # Get members
        result = await session.execute(
            select(OrganizationMember).where(OrganizationMember.org_id == org_id)
        )
        members = [
            {
                "user_id": m.user_id,
                "email": m.email,
                "name": m.name,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None
            }
            for m in result.scalars().all()
        ]
        
        return {
            "organization": {
                "org_id": org.org_id,
                "name": org.name,
                "slug": org.slug,
                "owner_id": org.owner_id,
                "website_url": org.website_url,
                "industry": org.industry,
                "logo_url": org.logo_url,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "members": members
            }
        }


@router.put("/{org_id}")
async def update_organization(org_id: str, data: OrganizationUpdate, user: dict = Depends(get_current_user)):
    """Update organization - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import Organization, OrganizationMember
    
    async with async_session_maker() as session:
        # Check if user is owner or admin
        result = await session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
            .where(OrganizationMember.user_id == user["user_id"])
            .where(OrganizationMember.role.in_(["owner", "admin"]))
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Droits insuffisants")
        
        # Update organization
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            await session.execute(
                update(Organization)
                .where(Organization.org_id == org_id)
                .values(**update_data)
            )
            await session.commit()
        
        return {"message": "Organisation mise à jour"}


@router.delete("/{org_id}")
async def delete_organization(org_id: str, user: dict = Depends(get_current_user)):
    """Delete organization - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import Organization
    
    async with async_session_maker() as session:
        # Check if user is owner
        result = await session.execute(
            select(Organization)
            .where(Organization.org_id == org_id)
            .where(Organization.owner_id == user["user_id"])
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Seul le propriétaire peut supprimer l'organisation")
        
        # Delete organization (cascade will delete members)
        await session.execute(
            delete(Organization).where(Organization.org_id == org_id)
        )
        await session.commit()
        
        return {"message": "Organisation supprimée"}


@router.post("/{org_id}/members")
async def invite_member(org_id: str, data: InviteMember, user: dict = Depends(get_current_user)):
    """Invite a member to organization - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import Organization, OrganizationMember, OrganizationInvite
    
    async with async_session_maker() as session:
        # Check if user can invite (owner or admin)
        result = await session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
            .where(OrganizationMember.user_id == user["user_id"])
            .where(OrganizationMember.role.in_(["owner", "admin"]))
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Droits insuffisants pour inviter")
        
        # Check if already a member
        result = await session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
            .where(OrganizationMember.email == data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Cet utilisateur est déjà membre")
        
        # Create invite
        import secrets
        invite_token = secrets.token_urlsafe(32)
        invite = OrganizationInvite(
            invite_id=f"inv_{uuid.uuid4().hex[:12]}",
            org_id=org_id,
            email=data.email,
            role=data.role,
            token=invite_token,
            invited_by=user["user_id"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        session.add(invite)
        await session.commit()
        
        # TODO: Send invitation email
        
        return {
            "message": "Invitation envoyée",
            "invite_token": invite_token
        }


@router.post("/invites/accept")
async def accept_invite(data: AcceptInvite, user: dict = Depends(get_current_user)):
    """Accept organization invite - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import OrganizationMember, OrganizationInvite
    
    async with async_session_maker() as session:
        # Find invite
        result = await session.execute(
            select(OrganizationInvite)
            .where(OrganizationInvite.token == data.token)
            .where(OrganizationInvite.status == "pending")
        )
        invite = result.scalar_one_or_none()
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation non trouvée ou expirée")
        
        # Check if expired
        if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Cette invitation a expiré")
        
        # Add user as member
        member = OrganizationMember(
            member_id=f"mem_{uuid.uuid4().hex[:12]}",
            org_id=invite.org_id,
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            role=invite.role
        )
        session.add(member)
        
        # Mark invite as accepted
        await session.execute(
            update(OrganizationInvite)
            .where(OrganizationInvite.invite_id == invite.invite_id)
            .values(status="accepted", accepted_at=datetime.now(timezone.utc))
        )
        
        await session.commit()
        
        return {"message": "Vous avez rejoint l'organisation"}


@router.delete("/{org_id}/members/{member_user_id}")
async def remove_member(org_id: str, member_user_id: str, user: dict = Depends(get_current_user)):
    """Remove member from organization - PostgreSQL version"""
    from ..db.database import async_session_maker
    from ..db.models import Organization, OrganizationMember
    
    async with async_session_maker() as session:
        # Check permissions
        result = await session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
            .where(OrganizationMember.user_id == user["user_id"])
            .where(OrganizationMember.role.in_(["owner", "admin"]))
        )
        requester = result.scalar_one_or_none()
        
        if not requester:
            raise HTTPException(status_code=403, detail="Droits insuffisants")
        
        # Cannot remove owner
        result = await session.execute(
            select(Organization).where(Organization.org_id == org_id)
        )
        org = result.scalar_one_or_none()
        if org and org.owner_id == member_user_id:
            raise HTTPException(status_code=400, detail="Impossible de retirer le propriétaire")
        
        # Remove member
        await session.execute(
            delete(OrganizationMember)
            .where(OrganizationMember.org_id == org_id)
            .where(OrganizationMember.user_id == member_user_id)
        )
        await session.commit()
        
        return {"message": "Membre retiré"}
