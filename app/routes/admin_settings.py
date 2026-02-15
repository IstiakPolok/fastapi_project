from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin import Admin
from app.models.settings import PrivacyPolicy, TermsOfService
from app.schemas.settings import (
    PrivacyPolicyUpdate, PrivacyPolicyResponse,
    TermsOfServiceUpdate, TermsOfServiceResponse
)
from app.core.admin_dependencies import get_current_admin

router = APIRouter(prefix="/api/admin/settings", tags=["Admin - Settings"])


# Privacy Policy Endpoints
@router.get("/privacy-policy", response_model=PrivacyPolicyResponse)
async def get_privacy_policy(db: Session = Depends(get_db)):
    """Get the current privacy policy (public endpoint)"""
    policy = db.query(PrivacyPolicy).order_by(PrivacyPolicy.id.desc()).first()
    if not policy:
        # Return default empty policy
        return PrivacyPolicyResponse(
            id=0,
            content="Privacy policy not yet configured.",
            version="1.0",
            updated_at=None,
            updated_by=None
        )
    return policy


@router.put("/privacy-policy", response_model=PrivacyPolicyResponse)
async def update_privacy_policy(
    policy_data: PrivacyPolicyUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Update or create privacy policy"""
    policy = db.query(PrivacyPolicy).order_by(PrivacyPolicy.id.desc()).first()
    
    if policy:
        # Update existing
        policy.content = policy_data.content
        if policy_data.version:
            policy.version = policy_data.version
        policy.updated_by = admin.id
    else:
        # Create new
        policy = PrivacyPolicy(
            content=policy_data.content,
            version=policy_data.version or "1.0",
            updated_by=admin.id
        )
        db.add(policy)
    
    db.commit()
    db.refresh(policy)
    
    return policy


# Terms of Service Endpoints
@router.get("/terms-of-service", response_model=TermsOfServiceResponse)
async def get_terms_of_service(db: Session = Depends(get_db)):
    """Get the current terms of service (public endpoint)"""
    terms = db.query(TermsOfService).order_by(TermsOfService.id.desc()).first()
    if not terms:
        return TermsOfServiceResponse(
            id=0,
            content="Terms of service not yet configured.",
            version="1.0",
            updated_at=None,
            updated_by=None
        )
    return terms


@router.put("/terms-of-service", response_model=TermsOfServiceResponse)
async def update_terms_of_service(
    terms_data: TermsOfServiceUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Update or create terms of service"""
    terms = db.query(TermsOfService).order_by(TermsOfService.id.desc()).first()
    
    if terms:
        terms.content = terms_data.content
        if terms_data.version:
            terms.version = terms_data.version
        terms.updated_by = admin.id
    else:
        terms = TermsOfService(
            content=terms_data.content,
            version=terms_data.version or "1.0",
            updated_by=admin.id
        )
        db.add(terms)
    
    db.commit()
    db.refresh(terms)
    
    return terms
