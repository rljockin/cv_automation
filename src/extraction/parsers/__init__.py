#!/usr/bin/env python3
"""
CV Parser - Parse extracted text into structured data
Uses GenericCVParser for robust parsing across all CV formats
"""

from typing import Dict, List, Optional
from src.core import CVData, PersonalInfo, WorkExperience, Education, Language, ExtractionResult
from .generic_cv_parser import GenericCVParser

class CVParser:
    """Parse CV text into structured data"""
    
    def __init__(self):
        self.generic_parser = GenericCVParser()
    
    def parse_cv(self, extraction_result: ExtractionResult, filename: str = None):
        """Parse CV text into structured data using generic parser"""
        return self.generic_parser.parse_cv(extraction_result, filename)

__all__ = ['CVParser']