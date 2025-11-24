#!/usr/bin/env python3
"""
Hybrid Parsing Strategy
Combines pattern-based structure detection with AI-powered content extraction
Target: 85% success rate, 1-3 seconds per CV, cost-effective
"""

from typing import Dict
from src.core.logger import setup_logger
from .pattern_strategy import PatternStrategy
from .openai_strategy import OpenAIStrategy

class HybridStrategy:
    """
    Hybrid parser combining pattern-based and AI approaches
    
    Strategy:
    1. Use patterns to detect structure (fast, free)
    2. Use AI to extract detailed content (accurate, paid)
    3. Merge results for best of both worlds
    
    Benefits:
    - Faster than pure AI (structure detection is instant)
    - More accurate than pure patterns (content extraction by AI)
    - Cost-effective (only AI for complex parts)
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing HybridStrategy...")
        
        # Initialize both strategies
        self.pattern_strategy = PatternStrategy()
        self.openai_strategy = OpenAIStrategy()
        
        self.logger.info("HybridStrategy initialized with both pattern and AI strategies")
    
    def parse(self, cv_text: str, filename: str) -> Dict:
        """
        Parse CV using hybrid approach
        
        Args:
            cv_text: Full CV text
            filename: Original filename
            
        Returns:
            Dictionary with extracted data
        """
        self.logger.info(f"Starting hybrid parsing for {filename}")
        
        try:
            # Step 1: Quick pattern-based extraction for structure
            pattern_result = self.pattern_strategy.parse(cv_text, filename)
            pattern_confidence = pattern_result.get('confidence_score', 0.0)
            
            self.logger.debug(f"Pattern extraction confidence: {pattern_confidence:.2f}")
            
            # Step 2: Decide if AI is needed
            if pattern_confidence >= 0.8:
                # Pattern extraction is good enough
                self.logger.info(f"Pattern extraction sufficient (confidence: {pattern_confidence:.2f})")
                return pattern_result
            
            # Step 3: Use AI for better accuracy
            self.logger.info("Pattern confidence low, using AI for detailed extraction")
            ai_result = self.openai_strategy.parse(cv_text, filename)
            ai_confidence = ai_result.get('confidence_score', 0.0)
            
            self.logger.debug(f"AI extraction confidence: {ai_confidence:.2f}")
            
            # Step 4: Choose best result
            if ai_confidence > pattern_confidence:
                self.logger.info(f"Using AI result (confidence: {ai_confidence:.2f} > {pattern_confidence:.2f})")
                return ai_result
            else:
                self.logger.info(f"Using pattern result (confidence: {pattern_confidence:.2f} >= {ai_confidence:.2f})")
                return pattern_result
                
        except Exception as e:
            self.logger.error(f"Hybrid parsing failed: {str(e)}", exc_info=True)
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

__all__ = ['HybridStrategy']

