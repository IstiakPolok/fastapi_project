from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminLogin, AdminResponse, AdminToken, AdminProfileResponse, AdminProfileUpdate, AdminChangePassword
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.admin_dependencies import get_current_admin
from app.core.file_upload import get_profile_image_url
from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin Authentication"])


@router.post("/change-password")
async def admin_change_password(
    password_data: AdminChangePassword,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Change current admin's password"""
    # 1. Verify current password
    if not verify_password(password_data.current_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # 2. Check new passwords match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
        
    # 3. Update password
    current_admin.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/profile", response_model=AdminProfileResponse)
async def get_admin_profile(current_admin: Admin = Depends(get_current_admin)):
    """Fetch the currently logged-in admin's profile"""
    current_admin.profile_image_url = get_profile_image_url(current_admin.profile_image)
    return current_admin


@router.patch("/profile", response_model=AdminProfileResponse)
async def update_admin_profile(
    profile_data: AdminProfileUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update the currently logged-in admin's profile"""
    # Check if email is being changed and if it already exists
    if profile_data.email and profile_data.email != current_admin.email:
        existing_admin = db.query(Admin).filter(Admin.email == profile_data.email).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_admin.email = profile_data.email
    
    # Update name if provided
    if profile_data.name:
        current_admin.name = profile_data.name
        
    db.commit()
    db.refresh(current_admin)
    current_admin.profile_image_url = get_profile_image_url(current_admin.profile_image)
    return current_admin


@router.post("/signup", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def admin_signup(admin_data: AdminCreate, db: Session = Depends(get_db)):
    """Create a new admin account"""
    # Validate password confirmation
    if admin_data.password != admin_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check if admin already exists
    existing_admin = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if this is the first admin (make them superadmin)
    is_first_admin = db.query(Admin).count() == 0
    
    # Create new admin
    hashed_password = get_password_hash(admin_data.password)
    new_admin = Admin(
        name=admin_data.name,
        email=admin_data.email,
        hashed_password=hashed_password,
        is_superadmin=is_first_admin,
        is_active=True
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return new_admin


@router.post("/login", response_model=AdminToken)
async def admin_login(admin_data: AdminLogin, db: Session = Depends(get_db)):
    """Admin login and return JWT token"""
    # Find admin
    admin = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(admin_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if admin is active
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled"
        )
    
    # Create access token with admin type
    access_token = create_access_token(
        data={"sub": admin.email, "type": "admin"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
