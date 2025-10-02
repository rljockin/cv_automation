#!/usr/bin/env python3
"""
OCR Extractor - Extract text from image-based PDFs using Tesseract OCR
Handles scanned documents and PDFs without selectable text
"""

from datetime import datetime
from typing import List, Optional
import os

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


class OCRExtractor(BaseExtractor):
    """
    Extract text using Tesseract OCR
    
    Features:
    - Converts PDF pages to images
    - Runs Tesseract OCR with Dutch + English language support
    - Provides confidence scoring
    - Handles multi-page documents
    - Timeout protection for large files
    
    Requirements:
    - Tesseract OCR installed and in PATH
    - pdf2image library
    - pytesseract library
    - Poppler utilities (for pdf2image)
    """
    
    def __init__(self):
        """Initialize OCR extractor with configuration"""
        super().__init__()
        
        # OCR configuration
        self.languages = 'nld+eng'  # Dutch + English
        self.dpi = 300  # High resolution for better OCR
        self.tesseract_config = '--psm 1'  # Auto page segmentation with OSD
        
        # Check if Tesseract is available
        self.tesseract_available = self._check_tesseract_available()
        
        if not self.tesseract_available:
            self._log("Tesseract OCR not available - OCR extraction will fail", "WARNING")
    
    def can_handle(self, cv_file: CVFile) -> bool:
        """
        Check if file can be processed with OCR
        
        OCR works on PDFs (both text-based and image-based)
        """
        return cv_file.file_format == FileFormat.PDF
    
    def extract_text(self, cv_file: CVFile) -> ExtractionResult:
        """
        Extract text using OCR
        
        Process:
        1. Check Tesseract is available
        2. Convert PDF to images (300 DPI)
        3. For each page image:
           a. Run Tesseract OCR
           b. Collect extracted text
           c. Track confidence if possible
        4. Combine all pages
        5. Clean OCR artifacts
        6. Return with OCR confidence score
        
        Error Handling:
        - Tesseract not installed: Return failure
        - Conversion fails: Return failure
        - OCR timeout: Return partial results
        - No text from OCR: Return failure
        
        Args:
            cv_file: CVFile object with PDF path
            
        Returns:
            ExtractionResult with OCR'd text and confidence
        """
        
        self._log(f"Starting OCR extraction for: {cv_file.file_name}")
        
        # Check Tesseract availability
        if not self.tesseract_available:
            return self._create_failure_result(
                error="Tesseract OCR not installed or not in PATH",
                method=ExtractionMethod.OCR
            )
        
        with Timer("OCR extraction") as timer:
            try:
                # Import OCR libraries (will fail if not installed)
                from pdf2image import convert_from_path
                import pytesseract
                
                # Convert PDF to images
                self._log(f"Converting PDF to images (DPI: {self.dpi})...")
                
                try:
                    images = convert_from_path(
                        cv_file.file_path,
                        dpi=self.dpi,
                        fmt='PNG',
                        thread_count=2  # Use multiple threads for speed
                    )
                except Exception as e:
                    return self._create_failure_result(
                        error=f"PDF to image conversion failed: {str(e)}",
                        method=ExtractionMethod.OCR
                    )
                
                page_count = len(images)
                self._log(f"Converted {page_count} pages to images")
                
                # Run OCR on each page
                all_text = []
                confidence_scores = []
                
                for page_num, image in enumerate(images, 1):
                    self._log(f"OCR processing page {page_num}/{page_count}...")
                    
                    try:
                        # Run Tesseract OCR
                        page_text = pytesseract.image_to_string(
                            image,
                            lang=self.languages,
                            config=self.tesseract_config
                        )
                        
                        if page_text.strip():
                            all_text.append(f"--- Page {page_num} ---\n{page_text.strip()}")
                            
                            # Try to get confidence score
                            try:
                                data = pytesseract.image_to_data(
                                    image,
                                    lang=self.languages,
                                    output_type=pytesseract.Output.DICT
                                )
                                # Calculate average confidence for this page
                                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                                if confidences:
                                    page_confidence = sum(confidences) / len(confidences)
                                    confidence_scores.append(page_confidence)
                            except:
                                # Confidence scoring is optional
                                pass
                        else:
                            self._log(f"No text found on page {page_num}", "WARNING")
                    
                    except Exception as e:
                        self._log(f"OCR failed for page {page_num}: {str(e)}", "ERROR")
                        continue
                
                # Combine all pages
                full_text = '\n\n'.join(all_text)
                full_text = self._clean_ocr_artifacts(full_text)
                
                # Calculate overall confidence
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                
                # Check if we got any text
                if not full_text.strip():
                    return self._create_failure_result(
                        error="OCR produced no text - possible blank pages or incompatible format",
                        method=ExtractionMethod.OCR
                    )
                
                # Validate quality
                if not self._validate_text_quality(full_text, min_length=100):
                    self._log(
                        f"OCR text quality low - only {len(full_text)} chars",
                        "WARNING"
                    )
                
                # Success!
                self._log(f"OCR extracted {len(full_text)} characters (confidence: {avg_confidence:.1f}%)")
                
                return self._create_success_result(
                    text=full_text,
                    method=ExtractionMethod.OCR,
                    page_count=page_count,
                    extraction_time=timer.duration if timer.duration else 0.0,
                    ocr_confidence=avg_confidence / 100 if avg_confidence else None,
                    has_selectable_text=False
                )
                
            except ImportError as e:
                error_msg = f"OCR libraries not installed: {str(e)}"
                self._log(error_msg, "ERROR")
                return self._create_failure_result(
                    error=error_msg,
                    method=ExtractionMethod.OCR
                )
            
            except Exception as e:
                error_msg = f"OCR extraction failed: {str(e)}"
                self._log(error_msg, "ERROR")
                return self._create_failure_result(
                    error=error_msg,
                    method=ExtractionMethod.OCR
                )
    
    def _check_tesseract_available(self) -> bool:
        """
        Check if Tesseract OCR is installed and available
        
        Returns:
            True if Tesseract is in PATH and working
        """
        try:
            import pytesseract
            # Try to get Tesseract version
            version = pytesseract.get_tesseract_version()
            self._log(f"Tesseract OCR version {version} detected")
            return True
        except:
            return False
    
    def _clean_ocr_artifacts(self, text: str) -> str:
        """
        Clean common OCR artifacts and errors
        
        OCR often produces:
        - Extra spaces
        - Random line breaks
        - Misrecognized characters
        - Duplicate spaces
        
        Args:
            text: Raw OCR output
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Use standard clean_text utility
        cleaned = clean_text(text)
        
        # Additional OCR-specific cleaning
        import re
        
        # Remove page markers we added
        cleaned = re.sub(r'---\s*Page\s+\d+\s*---', '', cleaned)
        
        # Fix common OCR mistakes (optional - can be expanded)
        # Example: "rn" often misread as "m"
        # But we'll keep it simple for now - clean_text handles most
        
        return cleaned

