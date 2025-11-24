"""
Results Endpoint - Get Processing Results
"""

import os
import sys
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.database import get_database
from src.core.logger import setup_logger
from API.auth.api_key import verify_api_key

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/results/{cv_id}")
async def get_results(
    cv_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get processing results for a CV
    
    - **cv_id**: CV identifier
    
    Returns extracted data and file information
    """
    db = get_database()
    
    # Get CV file record
    cv_record = db.get_cv_file(cv_id)
    
    if not cv_record:
        raise HTTPException(status_code=404, detail="CV not found")
    
    # Get processing results
    processing_results = db.get_processing_results(cv_id)
    
    if not processing_results:
        raise HTTPException(status_code=404, detail="No processing results found")
    
    latest_result = processing_results[-1]
    
    return {
        "cv_id": cv_id,
        "file_name": cv_record['file_name'],
        "status": cv_record['status'],
        "confidence_score": latest_result.confidence_score,
        "processing_time": latest_result.processing_time,
        "download_url": f"/api/download/{cv_id}",
        "output_file": latest_result.output_file_path,
        "validation_issues": latest_result.validation_issues,
        "processed_date": cv_record['processed_date'].isoformat() if cv_record['processed_date'] else None
    }


@router.get("/download/{cv_id}")
async def download_resume(
    cv_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Download generated Resumé
    
    - **cv_id**: CV identifier
    
    Returns the generated Resumé file
    """
    db = get_database()
    
    # Get processing results
    processing_results = db.get_processing_results(cv_id)
    
    if not processing_results:
        raise HTTPException(status_code=404, detail="No results found")
    
    latest_result = processing_results[-1]
    output_path = latest_result.output_file_path
    
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        output_path,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=os.path.basename(output_path)
    )

