from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminLogin, AdminResponse, AdminToken
from app.core.security import verify_password, get_password_hash, create_access_token
from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin Authentication"])


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
