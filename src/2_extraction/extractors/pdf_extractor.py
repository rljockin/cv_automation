#!/usr/bin/env python3
"""
PDF Extractor - Extract text from PDF files
Handles text-based PDFs with fallback to OCR for image-based files
"""

import PyPDF2
from datetime import datetime
from typing import List

from src.core import (
    ExtractionResult,
    ExtractionMethod,
    FileFormat,
    CVFile,
    Timer,
    ProcessingConfig,
    clean_text,
)
from .base_extractor import BaseExtractor


class PDFExtractor(BaseExtractor):
    """
    Extract text from PDF files
    
    Features:
    - Extracts selectable text from text-based PDFs
    - Detects image-only PDFs (flags for OCR)
    - Page-by-page extraction
    - Handles encrypted/protected PDFs
    - Robust error handling
    
    Strategy:
    - Try standard text extraction first
    - If text yield is low (<100 chars) → flag for OCR
    - If extraction fails → return error
    """
    
    def can_handle(self, cv_file: CVFile) -> bool:
        """Check if file is PDF format"""
        return cv_file.file_format == FileFormat.PDF
    
    def extract_text(self, cv_file: CVFile) -> ExtractionResult:
        """
        Extract text from PDF file
        
        Extraction Process:
        1. Open PDF with PyPDF2
        2. Get page count
        3. Extract text from each page
        4. Combine all pages
        5. Check if text yield is sufficient
        6. If text < threshold → flag for OCR
        7. Return ExtractionResult
        
        Quality Checks:
        - If extracted text < 100 chars → likely image-based PDF
        - If no text at all → definitely needs OCR
        - If some text but suspicious → warn but return what we have
        
        Args:
            cv_file: CVFile object with PDF path
            
        Returns:
            ExtractionResult with text or OCR flag
        """
        
        self._log(f"Extracting text from PDF: {cv_file.file_name}")
        
        with Timer("PDF extraction") as timer:
            try:
                # Open PDF file
                with open(cv_file.file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    # Check if encrypted
                    if pdf_reader.is_encrypted:
                        self._log("PDF is encrypted - attempting to decrypt", "WARNING")
                        try:
                            pdf_reader.decrypt('')  # Try empty password
                        except:
                            return self._create_failure_result(
                                error="PDF is encrypted and cannot be decrypted",
                                method=ExtractionMethod.PDF
                            )
                    
                    # Get page count
                    page_count = len(pdf_reader.pages)
                    self._log(f"PDF has {page_count} pages")
                    
                    # Extract text from each page
                    all_text = []
                    pages_with_text = 0
                    
                    for page_num in range(page_count):
                        page = pdf_reader.pages[page_num]
                        
                        # Try standard extraction
                        page_text = page.extract_text()
                        
                        if page_text and page_text.strip():
                            all_text.append(page_text.strip())
                            pages_with_text += 1
                    
                    # Combine all pages
                    full_text = '\n\n'.join(all_text)
                    full_text = clean_text(full_text)
                    
                    # Analyze extraction quality
                    text_length = len(full_text)
                    
                    self._log(f"Extracted {text_length} characters from {pages_with_text}/{page_count} pages")
                    
                    # Check if OCR is needed
                    if text_length < ProcessingConfig.OCR_THRESHOLD:
                        self._log(
                            f"Low text yield ({text_length} chars) - OCR recommended",
                            "WARNING"
                        )
                        
                        return self._create_failure_result(
                            error=f"Minimal text extracted ({text_length} chars) - likely image-based PDF requiring OCR",
                            method=ExtractionMethod.PDF,
                            partial_text=full_text
                        )
                    
                    # Check text quality
                    if not self._validate_text_quality(full_text, min_length=200):
                        self._log(
                            f"Text quality questionable - only {text_length} chars",
                            "WARNING"
                        )
                    
                    # Success!
                    self._log(f"Successfully extracted text from PDF")
                    
                    return self._create_success_result(
                        text=full_text,
                        method=ExtractionMethod.PDF,
                        page_count=page_count,
                        extraction_time=timer.duration if timer.duration else 0.0,
                    )
                    
            except Exception as e:
                error_msg = f"PDF extraction failed: {str(e)}"
                self._log(error_msg, "ERROR")
                
                return self._create_failure_result(
                    error=error_msg,
                    method=ExtractionMethod.PDF
                )
    
    def _try_alternative_extraction(self, page) -> str:
        """
        Try alternative extraction methods for difficult PDFs
        
        Some PDFs need different extraction parameters
        
        Args:
            page: PDF page object
            
        Returns:
            Extracted text or empty string
        """
        try:
            # Method 1: Standard extraction
            text = page.extract_text()
            if text and text.strip():
                return text
            
            # Method 2: With visitor function (for complex layouts)
            text = page.extract_text(
                visitor_text=lambda text, cm, tm, fontDict, fontSize: text
            )
            if text and text.strip():
                return text
            
            # Method 3: Character by character (slower but more thorough)
            # This is a last resort
            # ... could implement if needed
            
        except:
            pass
        
        return ""

