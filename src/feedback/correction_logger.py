#!/usr/bin/env python3
"""
Correction Logger
Logs manual corrections for quality improvement
"""

from typing import Dict, Optional
from datetime import datetime

from src.core.database import get_database
from src.core.logger import setup_logger

logger = setup_logger(__name__)


class CorrectionLogger:
    """
    Logs manual corrections to extracted CV data
    Generic - works for any field correction
    """
    
    def __init__(self):
        self.db = get_database()
        logger.info("CorrectionLogger initialized")
    
    def log_correction(
        self,
        cv_id: str,
        field_corrected: str,
        original_value: Optional[str],
        corrected_value: str,
        corrected_by: str = "system",
        reason: Optional[str] = None
    ) -> bool:
        """
        Log a manual correction
        
        Args:
            cv_id: CV identifier
            field_corrected: Field that was corrected (e.g., 'name', 'birth_year')
            original_value: Original extracted value
            corrected_value: Corrected value
            corrected_by: Who made the correction
            reason: Optional reason for correction
            
        Returns:
            True if logged successfully
        """
        try:
            self.db.log_correction({
                'cv_id': cv_id,
                'field_corrected': field_corrected,
                'original_value': str(original_value) if original_value else None,
                'corrected_value': str(corrected_value),
                'corrected_by': corrected_by,
                'correction_reason': reason
            })
            
            logger.info(f"Correction logged for CV {cv_id}: {field_corrected}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log correction: {e}")
            return False
    
    def log_multiple_corrections(
        self,
        cv_id: str,
        corrections: Dict[str, tuple],
        corrected_by: str = "system"
    ) -> int:
        """
        Log multiple corrections at once
        
        Args:
            cv_id: CV identifier
            corrections: Dict of {field_name: (original_value, corrected_value)}
            corrected_by: Who made the corrections
            
        Returns:
            Number of corrections logged
        """
        count = 0
        
        for field, (original, corrected) in corrections.items():
            if self.log_correction(cv_id, field, original, corrected, corrected_by):
                count += 1
        
        logger.info(f"Logged {count} corrections for CV {cv_id}")
        return count
    
    def get_corrections(self, cv_id: Optional[str] = None, limit: int = 100) -> list:
        """
        Get logged corrections
        
        Args:
            cv_id: Optional CV ID to filter by
            limit: Maximum number of corrections to return
            
        Returns:
            List of correction records
        """
        try:
            corrections = self.db.get_corrections(cv_id=cv_id, limit=limit)
            
            return [{
                'id': c.id,
                'cv_id': c.cv_id,
                'field': c.field_corrected,
                'original': c.original_value,
                'corrected': c.corrected_value,
                'corrected_by': c.corrected_by,
                'reason': c.correction_reason,
                'timestamp': c.timestamp.isoformat()
            } for c in corrections]
            
        except Exception as e:
            logger.error(f"Failed to get corrections: {e}")
            return []


__all__ = ['CorrectionLogger']

