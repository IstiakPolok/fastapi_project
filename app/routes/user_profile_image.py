from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.file_upload import (
    save_upload_file,
    delete_file,
    get_profile_image_url,
    PROFILE_IMAGES_DIR,
    init_upload_directories
)

router = APIRouter(prefix="/api/user", tags=["User Profile Image"])

# Initialize upload directories
init_upload_directories()


@router.post("/profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload or update user profile image"""
    # Delete old profile image if exists
    if current_user.profile_image:
        delete_file(current_user.profile_image, PROFILE_IMAGES_DIR)
    
    # Save new image
    filename = await save_upload_file(file, PROFILE_IMAGES_DIR)
    
    # Update user record
    current_user.profile_image = filename
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile image uploaded successfully",
        "profile_image_url": get_profile_image_url(filename)
    }


@router.delete("/profile-image")
async def delete_profile_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user profile image"""
    if not current_user.profile_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile image to delete"
        )
    
    # Delete file
    delete_file(current_user.profile_image, PROFILE_IMAGES_DIR)
    
    # Update user record
    current_user.profile_image = None
    db.commit()
    
    return {"message": "Profile image deleted successfully"}
