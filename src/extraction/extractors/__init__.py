#!/usr/bin/env python3
"""
Extractors Package - Text extraction from various file formats
"""

from .base_extractor import BaseExtractor
from .docx_extractor import DOCXExtractor
from .pdf_extractor import PDFExtractor
from .ocr_extractor import OCRExtractor

class ExtractorFactory:
    """Factory to get appropriate extractor for file"""
    
    def __init__(self):
        self.extractors = [
            DOCXExtractor(),
            PDFExtractor(),
            OCRExtractor(),
        ]
    
    def get_extractor(self, cv_file):
        """Get appropriate extractor for file"""
        for extractor in self.extractors:
            if extractor.can_handle(cv_file):
                return extractor
        raise Exception(f"No extractor for {cv_file.file_format}")
    
    def extract(self, cv_file):
        """Extract text using appropriate extractor"""
        # Get primary extractor
        if cv_file.file_format.value == '.pdf':
            result = PDFExtractor().extract_text(cv_file)
            # If failed, try OCR
            if not result.success:
                result = OCRExtractor().extract_text(cv_file)
        else:
            extractor = self.get_extractor(cv_file)
            result = extractor.extract_text(cv_file)
        
        return result

__all__ = ['ExtractorFactory', 'BaseExtractor', 'DOCXExtractor', 'PDFExtractor', 'OCRExtractor']