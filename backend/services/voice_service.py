import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile

# Use a controlled temp processing directory
TEMP_UPLOAD_DIR = Path("uploads/audio/temp_processing")


def delegate_voice_processing(interaction_id: int, file: UploadFile) -> str:
    """
    Safely stores temporary audio and 'delegates' to the voice pipeline.
    Returns the processing state.
    """
    TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Safe UUID filename to avoid trusting original filename
    safe_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = TEMP_UPLOAD_DIR / safe_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Here we would delegate to Celery, Kafka, etc.
        # e.g., task_queue.send(file_path, interaction_id)
        
        # Simulated cleanup or passing responsibility to the worker
        # os.remove(file_path) 
    finally:
        file.file.close()
        
    return "RECEIVED"
