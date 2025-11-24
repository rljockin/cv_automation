"""
Health Check Endpoint
"""

from fastapi import APIRouter
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.database import get_database
from src.core.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/health")
async def health_check():
    """
    Check API health and component status
    
    Returns health status of all system components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.2.0",
        "components": {}
    }
    
    # Check database
    try:
        db = get_database()
        db.engine.connect()
        health_status["components"]["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = "error"
        health_status["status"] = "degraded"
    
    # Check extractor factory
    try:
        from src.extraction.extractors import ExtractorFactory
        ExtractorFactory()
        health_status["components"]["extractor"] = "ok"
    except Exception as e:
        logger.error(f"Extractor health check failed: {e}")
        health_status["components"]["extractor"] = "error"
        health_status["status"] = "degraded"
    
    # Check parser
    try:
        from openai_parser import OpenAICVParser
        parser = OpenAICVParser()
        health_status["components"]["parser"] = "ok"
    except Exception as e:
        logger.error(f"Parser health check failed: {e}")
        health_status["components"]["parser"] = "error"
        health_status["status"] = "degraded"
    
    # Check generator
    try:
        from template_resume_generator_v2 import TemplateResumeGeneratorV2
        if os.path.exists('2.docx'):
            TemplateResumeGeneratorV2('2.docx')
            health_status["components"]["generator"] = "ok"
        else:
            health_status["components"]["generator"] = "template_missing"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Generator health check failed: {e}")
        health_status["components"]["generator"] = "error"
        health_status["status"] = "degraded"
    
    return health_status

