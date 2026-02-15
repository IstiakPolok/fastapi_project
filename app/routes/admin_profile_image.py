from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin import Admin
from app.core.admin_dependencies import get_current_admin
from app.core.file_upload import (
    save_upload_file,
    delete_file,
    get_profile_image_url,
    PROFILE_IMAGES_DIR,
    init_upload_directories
)

router = APIRouter(prefix="/api/admin", tags=["Admin Profile Image"])

# Initialize upload directories
init_upload_directories()


@router.post("/profile-image")
async def upload_admin_profile_image(
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload or update admin profile image"""
    # Delete old profile image if exists
    if current_admin.profile_image:
        delete_file(current_admin.profile_image, PROFILE_IMAGES_DIR)
    
    # Save new image
    filename = await save_upload_file(file, PROFILE_IMAGES_DIR)
    
    # Update admin record
    current_admin.profile_image = filename
    db.commit()
    db.refresh(current_admin)
    
    return {
        "message": "Profile image uploaded successfully",
        "profile_image_url": get_profile_image_url(filename)
    }


@router.delete("/profile-image")
async def delete_admin_profile_image(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete admin profile image"""
    if not current_admin.profile_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile image to delete"
        )
    
    # Delete file
    delete_file(current_admin.profile_image, PROFILE_IMAGES_DIR)
    
    # Update admin record
    current_admin.profile_image = None
    db.commit()
    
    return {"message": "Profile image deleted successfully"}
