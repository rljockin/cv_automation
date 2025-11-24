"""
Status Endpoint - Check Processing Status
"""

import os
import sys
from fastapi import APIRouter, HTTPException, Depends

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.database import get_database
from src.core.logger import setup_logger
from API.auth.api_key import verify_api_key

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/status/{job_id}")
async def check_status(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Check the status of a processing job
    
    - **job_id**: Unique job identifier returned from upload
    
    Returns current status and progress
    """
    db = get_database()
    
    # Get CV file record
    cv_record = db.get_cv_file(job_id)
    
    if not cv_record:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get processing results
    processing_results = db.get_processing_results(job_id)
    
    # Build response (cv_record is now a dict)
    response = {
        "job_id": job_id,
        "status": cv_record['status'],
        "file_name": cv_record['file_name'],
        "progress": 100 if cv_record['status'] in ['completed', 'failed'] else 50,
        "confidence_score": cv_record['confidence_score'],
        "strategy_used": cv_record['strategy_used'],
        "needs_review": cv_record['needs_review'],
        "error_message": cv_record['error_message']
    }
    
    # Add result if completed
    if cv_record['status'] == 'completed' and processing_results:
        latest_result = processing_results[-1]
        response["result"] = {
            "output_file": latest_result.output_file_path,
            "download_url": f"/api/download/{job_id}",
            "confidence_score": latest_result.confidence_score,
            "processing_time": latest_result.processing_time
        }
    
    return response

