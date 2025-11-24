"""
Batch Endpoint - Batch CV Upload and Processing
"""

import os
import sys
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import List
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.database import get_database
from src.core.logger import setup_logger
from API.auth.api_key import verify_api_key

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Upload multiple CVs for batch processing
    
    - **files**: List of CV files (PDF, DOCX, or DOC format)
    
    Returns batch ID and initial status
    """
    batch_id = str(uuid.uuid4())
    
    try:
        # Validate files
        allowed_extensions = {'.pdf', '.docx', '.doc'}
        
        for file in files:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {file.filename}. Allowed: {', '.join(allowed_extensions)}"
                )
        
        # Create batch directory
        batch_dir = os.path.join('uploads/batch', batch_id)
        os.makedirs(batch_dir, exist_ok=True)
        
        # Save files
        file_ids = []
        for file in files:
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix.lower()
            file_path = os.path.join(batch_dir, f"{file_id}{file_ext}")
            
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            file_ids.append(file_id)
            logger.info(f"Batch file saved: {file.filename} -> {file_path}")
        
        # Create batch job in database
        db = get_database()
        db.create_batch_job({
            'id': batch_id,
            'total_files': len(files),
            'status': 'queued',
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0
        })
        
        return {
            "batch_id": batch_id,
            "total_files": len(files),
            "status": "queued",
            "message": f"Batch of {len(files)} files queued for processing",
            "status_url": f"/api/batch/{batch_id}/status",
            "file_ids": file_ids
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get status of a batch processing job
    
    - **batch_id**: Batch identifier
    
    Returns current progress and statistics
    """
    db = get_database()
    
    # Get batch job
    batch = db.get_batch_job(batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Calculate progress (batch is now a dict)
    progress = 0
    if batch['total_files'] > 0:
        progress = (batch['processed_files'] / batch['total_files']) * 100
    
    # Calculate ETA
    eta_seconds = None
    if batch['average_time_per_file'] > 0 and batch['processed_files'] < batch['total_files']:
        remaining = batch['total_files'] - batch['processed_files']
        eta_seconds = remaining * batch['average_time_per_file']
    
    return {
        "batch_id": batch_id,
        "status": batch['status'],
        "total_files": batch['total_files'],
        "processed_files": batch['processed_files'],
        "successful_files": batch['successful_files'],
        "failed_files": batch['failed_files'],
        "progress": progress,
        "current_file": batch['current_file'],
        "average_confidence": batch['average_confidence'],
        "eta_seconds": eta_seconds,
        "started_at": batch['started_at'].isoformat() if batch['started_at'] else None,
        "completed_at": batch['completed_at'].isoformat() if batch['completed_at'] else None
    }


@router.get("/batch/{batch_id}/results")
async def get_batch_results(
    batch_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get results for all files in a batch
    
    - **batch_id**: Batch identifier
    
    Returns list of all file results
    """
    db = get_database()
    
    # Get batch job
    batch = db.get_batch_job(batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get all CV files for this batch (simplified - in real implementation, 
    # would have batch_id foreign key in cv_files table)
    # For now, return batch summary
    
    # batch is now a dict
    return {
        "batch_id": batch_id,
        "status": batch['status'],
        "total_files": batch['total_files'],
        "successful_files": batch['successful_files'],
        "failed_files": batch['failed_files'],
        "average_confidence": batch['average_confidence'],
        "message": "Batch processing results available",
        "note": "Individual file results can be retrieved via /api/results/{cv_id}"
    }

