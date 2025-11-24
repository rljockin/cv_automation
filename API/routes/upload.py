"""
Upload Endpoint - Single CV Upload
"""

import os
import sys
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.database import get_database
from src.core.logger import setup_logger
from src.core import CVFile, FileFormat
from src.extraction.extractors import ExtractorFactory
from openai_parser import OpenAICVParser
from template_resume_generator_v2 import TemplateResumeGeneratorV2
from API.auth.api_key import verify_api_key

router = APIRouter()
logger = setup_logger(__name__)

# Initialize components
extractor_factory = ExtractorFactory()
parser = OpenAICVParser()
generator = TemplateResumeGeneratorV2('2.docx') if os.path.exists('2.docx') else None


@router.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Upload and process a single CV
    
    - **file**: CV file (PDF, DOCX, or DOC format)
    
    Returns job ID and processing status
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file
        upload_dir = 'uploads/api'
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{job_id}{file_ext}")
        
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {file_path}")
        
        # Create CV file record
        cv_file = CVFile(
            id=job_id,
            person_name="API Upload",
            file_path=file_path,
            file_name=file.filename,
            file_format=FileFormat.from_extension(file_ext),
            file_size=len(content)
        )
        
        # Add to database
        db = get_database()
        db.add_cv_file({
            'id': job_id,
            'file_name': file.filename,
            'file_path': file_path,
            'file_format': file_ext,
            'file_size': len(content),
            'status': 'processing'
        })
        
        # Process CV (in background - simplified for now)
        try:
            # Extract
            extraction_result = extractor_factory.extract(cv_file)
            
            if not extraction_result.success:
                raise Exception(f"Extraction failed: {extraction_result.error}")
            
            # Parse
            cv_data = parser.parse_cv_text(extraction_result.text)
            
            if not cv_data:
                raise Exception("Parsing failed")
            
            # Generate
            output_dir = 'output/api'
            os.makedirs(output_dir, exist_ok=True)
            
            personal_info = cv_data.get('personal_info', {})
            output_filename = generator.format_resume_filename(personal_info) if generator else "Resumé_Synergie projectmanagement_Unknown.docx"
            output_path = os.path.join(output_dir, output_filename)
            
            if generator:
                gen_result = generator.generate_resume(cv_data, output_path)
                
                if gen_result['success']:
                    # Update database
                    db.update_cv_file(job_id, {
                        'status': 'completed',
                        'confidence_score': cv_data.get('confidence_score', 0.0),
                        'strategy_used': cv_data.get('strategy_used', 'openai')
                    })
                    
                    # Add processing result
                    db.add_processing_result({
                        'cv_id': job_id,
                        'processing_time': 0.0,
                        'extraction_success': True,
                        'parsing_success': True,
                        'generation_success': True,
                        'confidence_score': cv_data.get('confidence_score', 0.0),
                        'output_file_path': output_path
                    })
                    
                    return {
                        "job_id": job_id,
                        "status": "completed",
                        "message": "CV processed successfully",
                        "result": {
                            "person_name": person_name,
                            "confidence_score": cv_data.get('confidence_score', 0.0),
                            "download_url": f"/api/download/{job_id}"
                        }
                    }
                else:
                    raise Exception(f"Generation failed: {gen_result.get('error', 'Unknown')}")
            else:
                raise Exception("Generator not initialized")
                
        except Exception as e:
            logger.error(f"Processing failed for job {job_id}: {e}")
            
            # Update database with failure
            db.update_cv_file(job_id, {
                'status': 'failed',
                'error_message': str(e)
            })
            
            return {
                "job_id": job_id,
                "status": "failed",
                "message": "CV processing failed",
                "error": str(e)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

