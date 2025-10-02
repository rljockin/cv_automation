#!/usr/bin/env python3
"""
Language Detector - Detect Dutch/English/Mixed in CV text
Uses multiple detection strategies for robust language identification
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core import Language, clean_text


class DetectionMethod(str, Enum):
    """Language detection methods"""
    KEYWORDS = "keywords"
    PATTERNS = "patterns"
    STRUCTURE = "structure"
    COMBINED = "combined"


@dataclass
class LanguageScore:
    """Language detection score"""
    language: Language
    confidence: float
    method: DetectionMethod
    evidence: List[str]


class LanguageDetector:
    """
    Detect language in CV text using multiple strategies
    
    Detection Methods:
    1. Keywords - Common Dutch/English words
    2. Patterns - Language-specific patterns
    3. Structure - Section names and formatting
    4. Combined - Weighted combination
    
    Handles:
    - Pure Dutch CVs
    - Pure English CVs  
    - Mixed language CVs
    - CVs with minimal text
    """
    
    def __init__(self):
        """Initialize language detector with patterns"""
        
        # Dutch keywords (common in CVs)
        self.dutch_keywords = {
            'werkervaring', 'opleiding', 'vaardigheden', 'talen', 'software',
            'certificaten', 'cursussen', 'projecten', 'persoonlijke', 'gegevens',
            'naam', 'adres', 'telefoon', 'email', 'geboortedatum', 'nationaliteit',
            'rijbewijs', 'werkzaamheden', 'functie', 'bedrijf', 'periode',
            'verantwoordelijkheden', 'resultaten', 'ervaring', 'kennis',
            'hbo', 'wo', 'mbo', 'havo', 'vwo', 'universiteit', 'hogeschool',
            'nederland', 'nederlandse', 'nederlands', 'nederlandstalig',
            'januari', 'februari', 'maart', 'april', 'mei', 'juni',
            'juli', 'augustus', 'september', 'oktober', 'november', 'december',
            'heden', 'tot', 'vanaf', 'sinds', 'van', 'tot', 'tussen',
            'projectmanager', 'consultant', 'engineer', 'specialist',
            'senior', 'junior', 'medior', 'leidinggevende', 'manager'
        }
        
        # English keywords (common in CVs)
        self.english_keywords = {
            'experience', 'education', 'skills', 'languages', 'software',
            'certificates', 'courses', 'projects', 'personal', 'information',
            'name', 'address', 'phone', 'email', 'birth', 'date', 'nationality',
            'license', 'responsibilities', 'results', 'knowledge', 'expertise',
            'university', 'college', 'degree', 'bachelor', 'master', 'phd',
            'england', 'english', 'american', 'international', 'global',
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'present', 'current', 'until', 'from', 'since', 'between',
            'project', 'manager', 'consultant', 'engineer', 'specialist',
            'senior', 'junior', 'lead', 'director', 'executive'
        }
        
        # Dutch section patterns
        self.dutch_sections = [
            r'(?i)^\s*(werkervaring|werk\s*ervaring|werk\s*geschiedenis)\s*$',
            r'(?i)^\s*(opleiding|onderwijs|educatie)\s*$',
            r'(?i)^\s*(vaardigheden|skills|competenties)\s*$',
            r'(?i)^\s*(talen|languages)\s*$',
            r'(?i)^\s*(software|programmeer\s*talen)\s*$',
            r'(?i)^\s*(certificaten|certificeringen)\s*$',
            r'(?i)^\s*(cursussen|trainingen)\s*$',
            r'(?i)^\s*(projecten|project\s*ervaring)\s*$',
            r'(?i)^\s*(persoonlijke\s*gegevens|persoonlijke\s*informatie)\s*$',
            r'(?i)^\s*(profiel|over\s*mij|samenvatting)\s*$'
        ]
        
        # English section patterns
        self.english_sections = [
            r'(?i)^\s*(work\s*experience|professional\s*experience|employment)\s*$',
            r'(?i)^\s*(education|academic\s*background)\s*$',
            r'(?i)^\s*(skills|competencies|abilities)\s*$',
            r'(?i)^\s*(languages|language\s*skills)\s*$',
            r'(?i)^\s*(software|technical\s*skills)\s*$',
            r'(?i)^\s*(certificates|certifications)\s*$',
            r'(?i)^\s*(courses|training)\s*$',
            r'(?i)^\s*(projects|project\s*experience)\s*$',
            r'(?i)^\s*(personal\s*information|contact\s*details)\s*$',
            r'(?i)^\s*(profile|summary|about\s*me)\s*$'
        ]
        
        # Dutch date patterns
        self.dutch_date_patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',  # DD-MM-YYYY
            r'\b(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{4}\b',
            r'\b\d{4}\s*-\s*\d{4}\b',  # YYYY - YYYY
            r'\b\d{4}\s*-\s*heden\b',  # YYYY - heden
            r'\b\d{4}\s*tot\s*heden\b'  # YYYY tot heden
        ]
        
        # English date patterns
        self.english_date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
            r'\b\d{4}\s*-\s*\d{4}\b',  # YYYY - YYYY
            r'\b\d{4}\s*-\s*present\b',  # YYYY - present
            r'\b\d{4}\s*to\s*present\b'  # YYYY to present
        ]
    
    def detect_language(self, text: str) -> Language:
        """
        Detect language of CV text
        
        Args:
            text: Raw CV text
            
        Returns:
            Language enum (Dutch, English, Mixed, Unknown)
        """
        if not text or len(text.strip()) < 50:
            return Language.UNKNOWN
        
        # Clean text
        text = clean_text(text)
        
        # Get scores for each method
        scores = []
        
        # Method 1: Keywords
        keyword_score = self._detect_by_keywords(text)
        scores.append(keyword_score)
        
        # Method 2: Section patterns
        section_score = self._detect_by_sections(text)
        scores.append(section_score)
        
        # Method 3: Date patterns
        date_score = self._detect_by_dates(text)
        scores.append(date_score)
        
        # Method 4: Structure analysis
        structure_score = self._detect_by_structure(text)
        scores.append(structure_score)
        
        # Combine scores
        final_language = self._combine_scores(scores)
        
        return final_language
    
    def _detect_by_keywords(self, text: str) -> LanguageScore:
        """Detect language using keyword frequency"""
        
        # Count Dutch keywords
        dutch_count = 0
        dutch_evidence = []
        
        for keyword in self.dutch_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                dutch_count += len(matches)
                dutch_evidence.extend(matches[:3])  # Keep first 3 examples
        
        # Count English keywords
        english_count = 0
        english_evidence = []
        
        for keyword in self.english_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                english_count += len(matches)
                english_evidence.extend(matches[:3])  # Keep first 3 examples
        
        # Calculate confidence
        total_keywords = dutch_count + english_count
        if total_keywords == 0:
            return LanguageScore(Language.UNKNOWN, 0.0, DetectionMethod.KEYWORDS, [])
        
        dutch_ratio = dutch_count / total_keywords
        english_ratio = english_count / total_keywords
        
        if dutch_ratio > 0.7:
            return LanguageScore(Language.DUTCH, dutch_ratio, DetectionMethod.KEYWORDS, dutch_evidence)
        elif english_ratio > 0.7:
            return LanguageScore(Language.ENGLISH, english_ratio, DetectionMethod.KEYWORDS, english_evidence)
        else:
            return LanguageScore(Language.MIXED, max(dutch_ratio, english_ratio), DetectionMethod.KEYWORDS, 
                               dutch_evidence + english_evidence)
    
    def _detect_by_sections(self, text: str) -> LanguageScore:
        """Detect language using section headers"""
        
        lines = text.split('\n')
        dutch_sections = 0
        english_sections = 0
        dutch_evidence = []
        english_evidence = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check Dutch sections
            for pattern in self.dutch_sections:
                if re.match(pattern, line):
                    dutch_sections += 1
                    dutch_evidence.append(line)
                    break
            
            # Check English sections
            for pattern in self.english_sections:
                if re.match(pattern, line):
                    english_sections += 1
                    english_evidence.append(line)
                    break
        
        total_sections = dutch_sections + english_sections
        if total_sections == 0:
            return LanguageScore(Language.UNKNOWN, 0.0, DetectionMethod.PATTERNS, [])
        
        dutch_ratio = dutch_sections / total_sections
        english_ratio = english_sections / total_sections
        
        if dutch_ratio > 0.6:
            return LanguageScore(Language.DUTCH, dutch_ratio, DetectionMethod.PATTERNS, dutch_evidence)
        elif english_ratio > 0.6:
            return LanguageScore(Language.ENGLISH, english_ratio, DetectionMethod.PATTERNS, english_evidence)
        else:
            return LanguageScore(Language.MIXED, max(dutch_ratio, english_ratio), DetectionMethod.PATTERNS,
                               dutch_evidence + english_evidence)
    
    def _detect_by_dates(self, text: str) -> LanguageScore:
        """Detect language using date format patterns"""
        
        dutch_dates = 0
        english_dates = 0
        dutch_evidence = []
        english_evidence = []
        
        # Count Dutch date patterns
        for pattern in self.dutch_date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dutch_dates += len(matches)
            dutch_evidence.extend(matches[:2])  # Keep first 2 examples
        
        # Count English date patterns
        for pattern in self.english_date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            english_dates += len(matches)
            english_evidence.extend(matches[:2])  # Keep first 2 examples
        
        total_dates = dutch_dates + english_dates
        if total_dates == 0:
            return LanguageScore(Language.UNKNOWN, 0.0, DetectionMethod.PATTERNS, [])
        
        dutch_ratio = dutch_dates / total_dates
        english_ratio = english_dates / total_dates
        
        if dutch_ratio > 0.7:
            return LanguageScore(Language.DUTCH, dutch_ratio, DetectionMethod.PATTERNS, dutch_evidence)
        elif english_ratio > 0.7:
            return LanguageScore(Language.ENGLISH, english_ratio, DetectionMethod.PATTERNS, english_evidence)
        else:
            return LanguageScore(Language.MIXED, max(dutch_ratio, english_ratio), DetectionMethod.PATTERNS,
                               dutch_evidence + english_evidence)
    
    def _detect_by_structure(self, text: str) -> LanguageScore:
        """Detect language using structural patterns"""
        
        # Look for Dutch-specific structural elements
        dutch_indicators = 0
        english_indicators = 0
        evidence = []
        
        # Dutch postal code pattern
        if re.search(r'\b\d{4}\s*[A-Z]{2}\b', text):
            dutch_indicators += 2
            evidence.append("Dutch postal code")
        
        # Dutch phone pattern
        if re.search(r'\b0\d{1,2}[- ]?\d{6,8}\b', text):
            dutch_indicators += 2
            evidence.append("Dutch phone number")
        
        # English phone pattern (US/UK)
        if re.search(r'\b\+?\d{1,3}[- ]?\d{3,4}[- ]?\d{3,4}\b', text):
            english_indicators += 1
            evidence.append("International phone")
        
        # Dutch education terms
        dutch_edu = ['hbo', 'wo', 'mbo', 'havo', 'vwo', 'universiteit', 'hogeschool']
        for term in dutch_edu:
            if re.search(r'\b' + term + r'\b', text, re.IGNORECASE):
                dutch_indicators += 1
                evidence.append(f"Dutch education: {term}")
        
        # English education terms
        english_edu = ['bachelor', 'master', 'phd', 'university', 'college']
        for term in english_edu:
            if re.search(r'\b' + term + r'\b', text, re.IGNORECASE):
                english_indicators += 1
                evidence.append(f"English education: {term}")
        
        total_indicators = dutch_indicators + english_indicators
        if total_indicators == 0:
            return LanguageScore(Language.UNKNOWN, 0.0, DetectionMethod.STRUCTURE, [])
        
        dutch_ratio = dutch_indicators / total_indicators
        english_ratio = english_indicators / total_indicators
        
        if dutch_ratio > 0.6:
            return LanguageScore(Language.DUTCH, dutch_ratio, DetectionMethod.STRUCTURE, evidence)
        elif english_ratio > 0.6:
            return LanguageScore(Language.ENGLISH, english_ratio, DetectionMethod.STRUCTURE, evidence)
        else:
            return LanguageScore(Language.MIXED, max(dutch_ratio, english_ratio), DetectionMethod.STRUCTURE, evidence)
    
    def _combine_scores(self, scores: List[LanguageScore]) -> Language:
        """Combine multiple detection scores into final language"""
        
        if not scores:
            return Language.UNKNOWN
        
        # Weight different methods
        weights = {
            DetectionMethod.KEYWORDS: 0.4,    # Most reliable
            DetectionMethod.PATTERNS: 0.3,    # Section headers are strong indicators
            DetectionMethod.STRUCTURE: 0.2,   # Structural elements
            DetectionMethod.COMBINED: 0.1    # Fallback
        }
        
        # Calculate weighted scores
        language_scores = {
            Language.DUTCH: 0.0,
            Language.ENGLISH: 0.0,
            Language.MIXED: 0.0,
            Language.UNKNOWN: 0.0
        }
        
        for score in scores:
            weight = weights.get(score.method, 0.1)
            language_scores[score.language] += score.confidence * weight
        
        # Find language with highest score
        best_language = max(language_scores, key=language_scores.get)
        best_score = language_scores[best_language]
        
        # If score is too low, return unknown
        if best_score < 0.3:
            return Language.UNKNOWN
        
        return best_language
    
    def get_detection_details(self, text: str) -> Dict:
        """Get detailed language detection information"""
        
        if not text:
            return {"language": Language.UNKNOWN, "confidence": 0.0, "methods": []}
        
        text = clean_text(text)
        
        # Get individual scores
        keyword_score = self._detect_by_keywords(text)
        section_score = self._detect_by_sections(text)
        date_score = self._detect_by_dates(text)
        structure_score = self._detect_by_structure(text)
        
        # Final language
        final_language = self._combine_scores([keyword_score, section_score, date_score, structure_score])
        
        return {
            "language": final_language,
            "confidence": max(s.confidence for s in [keyword_score, section_score, date_score, structure_score]),
            "methods": [
                {
                    "method": score.method.value,
                    "language": score.language.value,
                    "confidence": score.confidence,
                    "evidence": score.evidence[:5]  # Limit evidence
                }
                for score in [keyword_score, section_score, date_score, structure_score]
            ]
        }
