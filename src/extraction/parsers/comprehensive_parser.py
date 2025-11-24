#!/usr/bin/env python3
"""
Comprehensive Multi-Strategy Parser
Orchestrates multiple parsing strategies with intelligent fallback
Target: 95% success rate through strategy combination
"""

from typing import Dict, List, Optional
from src.core.logger import setup_logger, log_error_with_context
from src.validation import DataValidator, ConfidenceScorer
from src.extraction.strategies import PatternStrategy, OpenAIStrategy, HybridStrategy

class ComprehensiveParser:
    """
    Comprehensive parser with multi-strategy fallback
    
    Strategy Chain:
    1. Try Hybrid first (fast + accurate, balanced cost)
    2. If low confidence, try pure OpenAI (slower, more accurate)
    3. If still low, try pattern-only (fast, free)
    4. If all fail, flag for manual review
    
    Target: 95%+ success rate by never giving up
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing ComprehensiveParser with multi-strategy approach...")
        
        # Configuration
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.auto_approve_threshold = self.config.get('auto_approve_threshold', 0.9)
        
        # Initialize all strategies
        try:
            self.hybrid_strategy = HybridStrategy()
            self.openai_strategy = OpenAIStrategy()
            self.pattern_strategy = PatternStrategy()
        except Exception as e:
            self.logger.error(f"Failed to initialize strategies: {e}")
            self.hybrid_strategy = None
            self.openai_strategy = None
            self.pattern_strategy = None
        
        # Initialize validation components
        self.validator = DataValidator()
        self.confidence_scorer = ConfidenceScorer()
        
        self.logger.info("ComprehensiveParser initialized successfully")
    
    def parse(self, cv_text: str, filename: str) -> Dict:
        """
        Parse CV using multi-strategy approach with fallbacks
        
        Args:
            cv_text: Full CV text
            filename: Original filename
            
        Returns:
            Best extraction result with confidence score
        """
        self.logger.info(f"Starting comprehensive parsing for {filename}")
        
        results = []
        
        # Strategy 1: Try Hybrid (balanced approach)
        if self.hybrid_strategy:
            try:
                self.logger.info("Trying Strategy 1: Hybrid (Pattern + AI)")
                hybrid_result = self.hybrid_strategy.parse(cv_text, filename)
                confidence = self.confidence_scorer.score(hybrid_result)
                hybrid_result['confidence_score'] = confidence
                hybrid_result['strategy_used'] = 'hybrid'
                
                results.append(('hybrid', confidence, hybrid_result))
                self.logger.info(f"Hybrid strategy confidence: {confidence:.2f}")
                
                # If confidence is excellent, use it
                if confidence >= self.auto_approve_threshold:
                    self.logger.info(f"Auto-approved with hybrid strategy (confidence: {confidence:.2f})")
                    return self._finalize_result(hybrid_result)
                    
            except Exception as e:
                log_error_with_context(self.logger, "Hybrid strategy failed", e, {'filename': filename})
        
        # Strategy 2: Try pure OpenAI if hybrid wasn't excellent
        if self.openai_strategy:
            try:
                self.logger.info("Trying Strategy 2: Pure OpenAI")
                openai_result = self.openai_strategy.parse(cv_text, filename)
                confidence = self.confidence_scorer.score(openai_result)
                openai_result['confidence_score'] = confidence
                openai_result['strategy_used'] = 'openai'
                
                results.append(('openai', confidence, openai_result))
                self.logger.info(f"OpenAI strategy confidence: {confidence:.2f}")
                
                # If confidence is good, use it
                if confidence >= self.confidence_threshold:
                    self.logger.info(f"Approved with OpenAI strategy (confidence: {confidence:.2f})")
                    return self._finalize_result(openai_result)
                    
            except Exception as e:
                log_error_with_context(self.logger, "OpenAI strategy failed", e, {'filename': filename})
        
        # Strategy 3: Try pure Pattern as last resort
        if self.pattern_strategy:
            try:
                self.logger.info("Trying Strategy 3: Pure Pattern (fallback)")
                pattern_result = self.pattern_strategy.parse(cv_text, filename)
                confidence = self.confidence_scorer.score(pattern_result)
                pattern_result['confidence_score'] = confidence
                pattern_result['strategy_used'] = 'pattern'
                
                results.append(('pattern', confidence, pattern_result))
                self.logger.info(f"Pattern strategy confidence: {confidence:.2f}")
                
            except Exception as e:
                log_error_with_context(self.logger, "Pattern strategy failed", e, {'filename': filename})
        
        # Choose best result
        if results:
            # Sort by confidence (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            best_strategy, best_confidence, best_result = results[0]
            
            self.logger.info(f"Best strategy: {best_strategy} with confidence {best_confidence:.2f}")
            
            # Even if confidence is low, return best we have
            if best_confidence >= 0.3:  # Minimum acceptable
                return self._finalize_result(best_result)
        
        # All strategies failed - flag for manual review
        self.logger.error(f"All parsing strategies failed for {filename}")
        return self._create_manual_review_result(filename)
    
    def _finalize_result(self, result: Dict) -> Dict:
        """
        Finalize and validate result
        
        Args:
            result: Raw extraction result
            
        Returns:
            Validated and cleaned result
        """
        # Validate data
        is_valid, issues = self.validator.validate_all(result)
        
        if not is_valid:
            self.logger.warning(f"Validation issues found: {issues}")
            result['validation_issues'] = issues
        else:
            result['validation_issues'] = []
        
        # Determine quality level
        quality = self.confidence_scorer.get_quality_level(result.get('confidence_score', 0.0))
        result['quality_level'] = quality
        
        # Determine if needs review
        needs_review = self.confidence_scorer.needs_review(result.get('confidence_score', 0.0))
        result['needs_review'] = needs_review
        
        return result
    
    def _create_manual_review_result(self, filename: str) -> Dict:
        """Create result flagged for manual review"""
        self.logger.warning(f"Flagging {filename} for manual review")
        
        return {
            'personal_info': {
                'full_name': f"MANUAL_REVIEW_{filename}",
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
            'confidence_score': 0.0,
            'strategy_used': 'none',
            'needs_review': True,
            'quality_level': 'failed',
            'manual_review_required': True,
            'validation_issues': ['All parsing strategies failed']
        }

__all__ = ['ComprehensiveParser']

