#!/usr/bin/env python3
"""
Extractors Module - Text extraction from various file formats
Provides factory pattern for selecting appropriate extractor
"""

from typing import Optional
from datetime import datetime

from src.core import (
    CVFile,
    ExtractionResult,
    FileFormat,
    UnsupportedDocumentException,
    TextExtractionFailedException,
)

from .base_extractor import BaseExtractor
from .docx_extractor import DOCXExtractor
from .pdf_extractor import PDFExtractor
from .ocr_extractor import OCRExtractor


class ExtractorFactory:
    """
    Factory for creating and managing text extractors
    
    Provides intelligent extractor selection based on:
    - File format
    - Previous extraction attempts
    - File characteristics
    
    Usage:
        factory = ExtractorFactory()
        result = factory.extract(cv_file)
    """
    
    def __init__(self, enable_ocr: bool = True):
        """
        Initialize factory with available extractors
        
        Args:
            enable_ocr: Whether to use OCR as fallback (default: True)
        """
        self.enable_ocr = enable_ocr
        
        # Initialize all extractors
        self.docx_extractor = DOCXExtractor()
        self.pdf_extractor = PDFExtractor()
        self.ocr_extractor = OCRExtractor() if enable_ocr else None
        
        # Extractor registry
        self.extractors = {
            FileFormat.DOCX: self.docx_extractor,
            FileFormat.DOC: self.docx_extractor,  # DOC uses same extractor
            FileFormat.PDF: self.pdf_extractor,
        }
    
    def extract(self, cv_file: CVFile) -> ExtractionResult:
        """
        Extract text using appropriate extractor with fallback strategy
        
        Strategy:
        1. Select primary extractor based on file format
        2. Attempt extraction
        3. If PDF extraction yields low text → try OCR
        4. Return result
        
        This is the MAIN entry point for text extraction.
        
        Args:
            cv_file: CVFile object
            
        Returns:
            ExtractionResult with text or error
            
        Raises:
            UnsupportedDocumentException: If file format not supported
        """
        
        # Get primary extractor
        extractor = self.get_extractor(cv_file)
        
        if not extractor:
            raise UnsupportedDocumentException(
                f"No extractor available for format: {cv_file.file_format}"
            )
        
        # Attempt extraction
        result = extractor.extract_text(cv_file)
        
        # For PDFs: If extraction failed or yielded little text, try OCR
        if cv_file.file_format == FileFormat.PDF and not result.success:
            if self.enable_ocr and self.ocr_extractor:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Falling back to OCR for {cv_file.file_name}")
                result = self.ocr_extractor.extract_text(cv_file)
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [WARNING] OCR disabled - cannot process image-based PDF")
        
        return result
    
    def get_extractor(self, cv_file: CVFile) -> Optional[BaseExtractor]:
        """
        Get appropriate extractor for file format
        
        Args:
            cv_file: CVFile object
            
        Returns:
            BaseExtractor instance or None if not supported
        """
        return self.extractors.get(cv_file.file_format)
    
    def get_extractor_by_format(self, file_format: FileFormat) -> Optional[BaseExtractor]:
        """
        Get extractor by file format enum
        
        Args:
            file_format: FileFormat enum
            
        Returns:
            BaseExtractor instance or None
        """
        return self.extractors.get(file_format)


# Convenience function for direct usage
def extract_text_from_cv(cv_file: CVFile, enable_ocr: bool = True) -> ExtractionResult:
    """
    Convenience function to extract text from a CV file
    
    Args:
        cv_file: CVFile object
        enable_ocr: Whether to use OCR fallback
        
    Returns:
        ExtractionResult
        
    Example:
        from src.extraction.extractors import extract_text_from_cv
        from src.core import CVFile, FileFormat
        
        cv_file = CVFile(...)
        result = extract_text_from_cv(cv_file)
        
        if result.success:
            print(f"Extracted {result.char_count} characters")
            print(result.text)
        else:
            print(f"Extraction failed: {result.error}")
    """
    factory = ExtractorFactory(enable_ocr=enable_ocr)
    return factory.extract(cv_file)


# Export all extractors and factory
__all__ = [
    'BaseExtractor',
    'DOCXExtractor',
    'PDFExtractor',
    'OCRExtractor',
    'ExtractorFactory',
    'extract_text_from_cv',
]

