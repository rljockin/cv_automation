#!/usr/bin/env python3
"""
Confidence Scorer - Calculate extraction quality score
Scores extracted data from 0.0 (no confidence) to 1.0 (high confidence)
"""

from typing import Dict
from src.core.logger import setup_logger

class ConfidenceScorer:
    """
    Calculate confidence score for extracted CV data
    Based on presence and quality of extracted fields
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Scoring weights (must sum to 1.0)
        self.weights = {
            'name': 0.25,
            'birth_year': 0.10,
            'work_experience': 0.30,
            'education': 0.20,
            'profile': 0.10,
            'skills': 0.05
        }
    
    def score(self, extracted_data: Dict) -> float:
        """
        Calculate overall confidence score
        
        Args:
            extracted_data: Dictionary with extracted CV data
            
        Returns:
            Confidence score 0.0-1.0
        """
        score = 0.0
        
        # 1. Name (25% weight)
        personal_info = extracted_data.get('personal_info', {})
        if self._has_valid_name(personal_info):
            score += self.weights['name']
            self.logger.debug("Name found: +0.25")
        
        # 2. Birth year (10% weight)
        if self._has_valid_birth_year(personal_info):
            score += self.weights['birth_year']
            self.logger.debug("Birth year found: +0.10")
        
        # 3. Work experience (30% weight)
        work_exp = extracted_data.get('work_experience', [])
        if work_exp and len(work_exp) > 0:
            # Scale based on number of entries
            work_score = min(len(work_exp) / 5.0, 1.0) * self.weights['work_experience']
            score += work_score
            self.logger.debug(f"Work experience ({len(work_exp)} entries): +{work_score:.2f}")
        
        # 4. Education (20% weight)
        education = extracted_data.get('education', [])
        if education and len(education) > 0:
            # Scale based on number of entries
            edu_score = min(len(education) / 3.0, 1.0) * self.weights['education']
            score += edu_score
            self.logger.debug(f"Education ({len(education)} entries): +{edu_score:.2f}")
        
        # 5. Profile/summary (10% weight)
        profile = extracted_data.get('profile_summary') or extracted_data.get('profile')
        if profile and len(str(profile)) > 50:  # At least 50 chars
            score += self.weights['profile']
            self.logger.debug("Profile found: +0.10")
        
        # 6. Skills (5% weight)
        skills = extracted_data.get('skills', [])
        if skills and len(skills) > 0:
            score += self.weights['skills']
            self.logger.debug(f"Skills ({len(skills)} items): +0.05")
        
        final_score = min(score, 1.0)
        self.logger.info(f"Confidence score: {final_score:.2f}")
        
        return final_score
    
    def _has_valid_name(self, personal_info: Dict) -> bool:
        """Check if name is present and looks valid"""
        name = personal_info.get('full_name')
        if not name:
            return False
        
        # Basic checks
        if len(name) < 3 or len(name) > 50:
            return False
        
        # Should not be a field label
        invalid_names = ['Naam', 'Name', 'Voornaam', 'Achternaam', 'Personalia']
        if name in invalid_names:
            return False
        
        return True
    
    def _has_valid_birth_year(self, personal_info: Dict) -> bool:
        """Check if birth year is present and valid"""
        birth_year = personal_info.get('birth_year')
        if not birth_year:
            return False
        
        try:
            year = int(birth_year)
            return 1940 <= year <= 2010
        except:
            return False
    
    def get_quality_level(self, score: float) -> str:
        """
        Convert score to quality level
        
        Returns:
            'excellent', 'good', 'acceptable', 'poor', 'failed'
        """
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.5:
            return 'acceptable'
        elif score >= 0.3:
            return 'poor'
        else:
            return 'failed'
    
    def should_auto_approve(self, score: float, threshold: float = 0.9) -> bool:
        """Determine if extraction is good enough for auto-approval"""
        return score >= threshold
    
    def needs_review(self, score: float, threshold: float = 0.7) -> bool:
        """Determine if extraction needs human review"""
        return 0.5 <= score < threshold

__all__ = ['ConfidenceScorer']

