"""File upload utilities for handling profile images"""
import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

# Upload directory configuration
UPLOAD_DIR = Path("uploads")
PROFILE_IMAGES_DIR = UPLOAD_DIR / "profile_images"

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def init_upload_directories():
    """Create upload directories if they don't exist"""
    PROFILE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )


async def save_upload_file(file: UploadFile, directory: Path) -> str:
    """
    Save uploaded file and return the filename
    
    Args:
        file: The uploaded file
        directory: Directory to save the file
        
    Returns:
        The saved filename
    """
    # Validate file
    validate_image_file(file)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = directory / unique_filename
    
    # Read and validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)
    
    return unique_filename


def delete_file(filename: str, directory: Path) -> bool:
    """
    Delete a file from the specified directory
    
    Args:
        filename: Name of the file to delete
        directory: Directory containing the file
        
    Returns:
        True if file was deleted, False if file didn't exist
    """
    if not filename:
        return False
        
    file_path = directory / filename
    if file_path.exists():
        file_path.unlink()
        return True
    return False


def get_profile_image_url(filename: Optional[str]) -> Optional[str]:
    """
    Get the URL for a profile image
    
    Args:
        filename: The image filename
        
    Returns:
        The URL path to access the image, or None if no filename
    """
    if not filename:
        return None
    return f"/uploads/profile_images/{filename}"
