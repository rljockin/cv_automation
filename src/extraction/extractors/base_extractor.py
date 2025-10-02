#!/usr/bin/env python3
"""
Base Extractor - Abstract interface for all text extractors
Defines the contract that all extractors must follow
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.core import (
    ExtractionResult,
    ExtractionMethod,
    CVFile,
    Timer,
)


class BaseExtractor(ABC):
    """Abstract base class for text extractors"""
    
    def __init__(self):
        """Initialize extractor"""
        self.name = self.__class__.__name__
    
    @abstractmethod
    def extract_text(self, cv_file: CVFile) -> ExtractionResult:
        """
        Extract text from a CV file
        
        Args:
            cv_file: CVFile object containing file path and metadata
            
        Returns:
            ExtractionResult with success status, extracted text, and metadata
            
        Raises:
            Should NOT raise exceptions - catch and return in ExtractionResult
        """
        pass
    
    @abstractmethod
    def can_handle(self, cv_file: CVFile) -> bool:
        """
        Check if this extractor can handle the given file
        
        Args:
            cv_file: CVFile object
            
        Returns:
            True if this extractor supports the file format
        """
        pass
    
    # =========================================================================
    # Helper Methods (available to all extractors)
    # =========================================================================
    
    def _create_success_result(
        self,
        text: str,
        method: ExtractionMethod,
        page_count: int = 0,
        extraction_time: float = 0.0,
        **kwargs
    ) -> ExtractionResult:
        """
        Create a successful extraction result
        
        Args:
            text: Extracted text
            method: Extraction method used
            page_count: Number of pages
            extraction_time: Time taken in seconds
            **kwargs: Additional metadata
            
        Returns:
            ExtractionResult with success=True
        """
        return ExtractionResult(
            success=True,
            text=text,
            method=method,
            page_count=page_count,
            char_count=len(text),
            word_count=len(text.split()),
            extraction_time=extraction_time,
            has_selectable_text=True,
            **kwargs
        )
    
    def _create_failure_result(
        self,
        error: str,
        method: ExtractionMethod,
        partial_text: str = "",
        **kwargs
    ) -> ExtractionResult:
        """
        Create a failed extraction result
        
        Args:
            error: Error message
            method: Extraction method attempted
            partial_text: Any text that was extracted (even if incomplete)
            **kwargs: Additional metadata
            
        Returns:
            ExtractionResult with success=False
        """
        return ExtractionResult(
            success=False,
            text=partial_text,
            method=method,
            error=error,
            **kwargs
        )
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message with timestamp
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [{self.name}] {message}")
    
    def _validate_text_quality(self, text: str, min_length: int = 50) -> bool:
        """
        Check if extracted text meets minimum quality standards
        
        Args:
            text: Extracted text
            min_length: Minimum acceptable character count
            
        Returns:
            True if text is acceptable quality
        """
        if not text:
            return False
        
        # Check length
        if len(text.strip()) < min_length:
            return False
        
        # Check if it's mostly valid characters (not garbage)
        printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
        if printable_chars / len(text) < 0.8:  # At least 80% printable
            return False
        
        return True

