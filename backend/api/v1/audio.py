"""
AAROH — Audio Ingestion API

Handles uploading of raw audio files.
Audio processing and ASR are NOT handled here (handled by voice pipeline).
"""

import os
import shutil
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from backend.core.security import get_current_user, require_role

router = APIRouter(tags=["Audio"])

# Local directory where audio files will be staged for the voice pipeline
UPLOAD_DIR = Path("uploads/audio")


@router.post(
    "/audio",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("caseworker"))],
)
def upload_audio(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Upload an audio file for a case interaction.
    The file is stored locally for the voice pipeline to process later.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
        
    try:
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save file safely
        file_path = UPLOAD_DIR / file.filename
        
        # In a real app we'd validate file type, size, generate a safe UUID filename, etc.
        # But this suffices for the Day 2 requirement of receiving and storing.
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "message": "Audio file uploaded successfully",
            "filename": file.filename,
            "path": str(file_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save audio file"
        )
    finally:
        file.file.close()
