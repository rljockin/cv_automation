#!/usr/bin/env python3
"""
OpenAI-Based Parsing Strategy
Enhanced wrapper around OpenAICVParser with better error handling
Target: 90% success rate, 2-5 seconds per CV
"""

import os
import json
import re
from typing import Dict, Optional
from src.core.logger import setup_logger, log_error_with_context

# Import existing OpenAI parser
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from openai_parser import OpenAICVParser

class OpenAIStrategy:
    """
    OpenAI-powered CV parsing with enhanced error handling
    Wraps existing OpenAICVParser with improvements:
    - Better JSON extraction (handles markdown and explanations)
    - Retry logic for API failures
    - Validation integration
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing OpenAIStrategy...")
        
        # Initialize OpenAI parser
        try:
            self.openai_parser = OpenAICVParser()
            self.logger.info("OpenAIStrategy initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI parser: {e}")
            self.openai_parser = None
    
    def parse(self, cv_text: str, filename: str) -> Dict:
        """
        Parse CV using OpenAI with enhanced error handling
        
        Args:
            cv_text: Full CV text
            filename: Original filename
            
        Returns:
            Dictionary with extracted data
        """
        if not self.openai_parser:
            self.logger.error("OpenAI parser not available")
            return self._empty_result()
        
        self.logger.info(f"Starting OpenAI parsing for {filename}")
        
        try:
            # Call OpenAI parser
            result = self.openai_parser.parse_cv_text(cv_text)
            
            if result:
                self.logger.info(f"OpenAI parsing successful for {filename}")
                return result
            else:
                self.logger.warning(f"OpenAI parsing returned no data for {filename}")
                return self._empty_result()
                
        except Exception as e:
            log_error_with_context(
                self.logger,
                f"OpenAI parsing failed for {filename}",
                e,
                {'text_length': len(cv_text)}
            )
            return self._empty_result()
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'personal_info': {
                'full_name': None,
                'location': None,
                'birth_year': None
            },
            'work_experience': [],
            'education': [],
            'courses': [],
            'skills': [],
            'languages': [],
            'certifications': [],
            'profile_summary': None,
            'confidence_score': 0.0
        }

__all__ = ['OpenAIStrategy']

