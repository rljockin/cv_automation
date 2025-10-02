#!/usr/bin/env python3
"""
Section Parser - Find and extract CV sections
Identifies section boundaries and extracts content for each section
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.core import Language, clean_text


@dataclass
class Section:
    """CV section with content"""
    name: str
    content: str
    start_line: int
    end_line: int
    confidence: float
    language: Language


class SectionParser:
    """
    Parse CV text into structured sections
    
    Handles:
    - Dutch section names (Werkervaring, Opleiding, etc.)
    - English section names (Work Experience, Education, etc.)
    - Mixed language CVs
    - Various section formats and styles
    - Missing or unclear sections
    
    Strategy:
    1. Detect language first
    2. Find section headers using patterns
    3. Extract content between sections
    4. Validate and clean sections
    """
    
    def __init__(self):
        """Initialize section parser with patterns"""
        
        # Dutch section patterns (case insensitive)
        self.dutch_sections = {
            'werkervaring': [
                r'(?i)^\s*(werkervaring|werk\s*ervaring|werk\s*geschiedenis|ervaring|carrière)\s*$',
                r'(?i)^\s*(werkervaring|werk\s*ervaring|werk\s*geschiedenis|ervaring|carrière)\s*:?\s*$'
            ],
            'opleiding': [
                r'(?i)^\s*(opleiding|onderwijs|educatie|studie|academische\s*achtergrond)\s*$',
                r'(?i)^\s*(opleiding|onderwijs|educatie|studie|academische\s*achtergrond)\s*:?\s*$'
            ],
            'vaardigheden': [
                r'(?i)^\s*(vaardigheden|skills|competenties|kennis|expertise)\s*$',
                r'(?i)^\s*(vaardigheden|skills|competenties|kennis|expertise)\s*:?\s*$'
            ],
            'talen': [
                r'(?i)^\s*(talen|languages|taal\s*kennis)\s*$',
                r'(?i)^\s*(talen|languages|taal\s*kennis)\s*:?\s*$'
            ],
            'software': [
                r'(?i)^\s*(software|programmeer\s*talen|it\s*vaardigheden|technische\s*vaardigheden)\s*$',
                r'(?i)^\s*(software|programmeer\s*talen|it\s*vaardigheden|technische\s*vaardigheden)\s*:?\s*$'
            ],
            'certificaten': [
                r'(?i)^\s*(certificaten|certificeringen|certificaties)\s*$',
                r'(?i)^\s*(certificaten|certificeringen|certificaties)\s*:?\s*$'
            ],
            'cursussen': [
                r'(?i)^\s*(cursussen|trainingen|opleidingen|studies)\s*$',
                r'(?i)^\s*(cursussen|trainingen|opleidingen|studies)\s*:?\s*$'
            ],
            'projecten': [
                r'(?i)^\s*(projecten|project\s*ervaring|project\s*geschiedenis)\s*$',
                r'(?i)^\s*(projecten|project\s*ervaring|project\s*geschiedenis)\s*:?\s*$'
            ],
            'persoonlijke_gegevens': [
                r'(?i)^\s*(persoonlijke\s*gegevens|persoonlijke\s*informatie|contact|gegevens)\s*$',
                r'(?i)^\s*(persoonlijke\s*gegevens|persoonlijke\s*informatie|contact|gegevens)\s*:?\s*$'
            ],
            'profiel': [
                r'(?i)^\s*(profiel|over\s*mij|samenvatting|persoonlijk\s*profiel)\s*$',
                r'(?i)^\s*(profiel|over\s*mij|samenvatting|persoonlijk\s*profiel)\s*:?\s*$'
            ]
        }
        
        # English section patterns (case insensitive)
        self.english_sections = {
            'work_experience': [
                r'(?i)^\s*(work\s*experience|professional\s*experience|employment|career)\s*$',
                r'(?i)^\s*(work\s*experience|professional\s*experience|employment|career)\s*:?\s*$'
            ],
            'education': [
                r'(?i)^\s*(education|academic\s*background|studies|qualifications)\s*$',
                r'(?i)^\s*(education|academic\s*background|studies|qualifications)\s*:?\s*$'
            ],
            'skills': [
                r'(?i)^\s*(skills|competencies|abilities|expertise)\s*$',
                r'(?i)^\s*(skills|competencies|abilities|expertise)\s*:?\s*$'
            ],
            'languages': [
                r'(?i)^\s*(languages|language\s*skills)\s*$',
                r'(?i)^\s*(languages|language\s*skills)\s*:?\s*$'
            ],
            'software': [
                r'(?i)^\s*(software|technical\s*skills|it\s*skills|programming)\s*$',
                r'(?i)^\s*(software|technical\s*skills|it\s*skills|programming)\s*:?\s*$'
            ],
            'certificates': [
                r'(?i)^\s*(certificates|certifications)\s*$',
                r'(?i)^\s*(certificates|certifications)\s*:?\s*$'
            ],
            'courses': [
                r'(?i)^\s*(courses|training|professional\s*development)\s*$',
                r'(?i)^\s*(courses|training|professional\s*development)\s*:?\s*$'
            ],
            'projects': [
                r'(?i)^\s*(projects|project\s*experience)\s*$',
                r'(?i)^\s*(projects|project\s*experience)\s*:?\s*$'
            ],
            'personal_information': [
                r'(?i)^\s*(personal\s*information|contact\s*details|contact)\s*$',
                r'(?i)^\s*(personal\s*information|contact\s*details|contact)\s*:?\s*$'
            ],
            'profile': [
                r'(?i)^\s*(profile|summary|about\s*me|personal\s*profile)\s*$',
                r'(?i)^\s*(profile|summary|about\s*me|personal\s*profile)\s*:?\s*$'
            ]
        }
        
        # Section priority (order matters for parsing)
        self.section_priority = [
            'persoonlijke_gegevens', 'personal_information',
            'profiel', 'profile',
            'werkervaring', 'work_experience',
            'opleiding', 'education',
            'vaardigheden', 'skills',
            'talen', 'languages',
            'software', 'software',
            'certificaten', 'certificates',
            'cursussen', 'courses',
            'projecten', 'projects'
        ]
    
    def parse_sections(self, text: str, language: Language = Language.UNKNOWN) -> Dict[str, Section]:
        """
        Parse CV text into sections
        
        Args:
            text: Raw CV text
            language: Detected language (optional)
            
        Returns:
            Dictionary mapping section names to Section objects
        """
        if not text or len(text.strip()) < 100:
            return {}
        
        # Clean text
        text = clean_text(text)
        lines = text.split('\n')
        
        # Find section headers
        section_headers = self._find_section_headers(lines, language)
        
        # Extract section content
        sections = self._extract_section_content(lines, section_headers)
        
        # Validate and clean sections
        sections = self._validate_sections(sections)
        
        return sections
    
    def _find_section_headers(self, lines: List[str], language: Language) -> List[Tuple[int, str, float]]:
        """
        Find section headers in text lines
        
        Args:
            lines: Text split into lines
            language: Detected language
            
        Returns:
            List of (line_number, section_name, confidence) tuples
        """
        headers = []
        
        # Choose section patterns based on language
        if language == Language.DUTCH:
            section_patterns = self.dutch_sections
        elif language == Language.ENGLISH:
            section_patterns = self.english_sections
        else:
            # Mixed or unknown - try both
            section_patterns = {**self.dutch_sections, **self.english_sections}
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Check if line matches any section pattern
            for section_name, patterns in section_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, line):
                        # Calculate confidence based on pattern match
                        confidence = self._calculate_header_confidence(line, pattern)
                        headers.append((line_num, section_name, confidence))
                        break
        
        # Sort by line number
        headers.sort(key=lambda x: x[0])
        
        return headers
    
    def _calculate_header_confidence(self, line: str, pattern: str) -> float:
        """Calculate confidence score for section header"""
        
        # Base confidence
        confidence = 0.8
        
        # Adjust based on line characteristics
        if len(line) > 50:  # Too long for a header
            confidence -= 0.3
        
        if line.isupper():  # All caps headers are common
            confidence += 0.1
        
        if ':' in line:  # Colon indicates section header
            confidence += 0.1
        
        # Check for common header formatting
        if re.match(r'^[A-Z\s]+$', line):  # All caps
            confidence += 0.1
        
        if re.match(r'^\d+\.?\s+', line):  # Numbered sections
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _extract_section_content(self, lines: List[str], headers: List[Tuple[int, str, float]]) -> Dict[str, Section]:
        """Extract content for each section"""
        
        sections = {}
        
        for i, (line_num, section_name, confidence) in enumerate(headers):
            # Determine end line
            if i + 1 < len(headers):
                end_line = headers[i + 1][0] - 1
            else:
                end_line = len(lines) - 1
            
            # Extract content
            content_lines = lines[line_num + 1:end_line + 1]
            content = '\n'.join(content_lines).strip()
            
            # Skip empty sections
            if not content or len(content) < 10:
                continue
            
            # Create section object
            section = Section(
                name=section_name,
                content=content,
                start_line=line_num,
                end_line=end_line,
                confidence=confidence,
                language=Language.UNKNOWN  # Will be set later
            )
            
            sections[section_name] = section
        
        return sections
    
    def _validate_sections(self, sections: Dict[str, Section]) -> Dict[str, Section]:
        """Validate and clean sections"""
        
        validated = {}
        
        for name, section in sections.items():
            # Clean content
            section.content = clean_text(section.content)
            
            # Skip if content is too short
            if len(section.content) < 20:
                continue
            
            # Check for duplicate content (might be parsing error)
            if self._is_duplicate_content(section.content, validated):
                continue
            
            # Adjust confidence based on content quality
            section.confidence = self._adjust_confidence(section)
            
            validated[name] = section
        
        return validated
    
    def _is_duplicate_content(self, content: str, existing_sections: Dict[str, Section]) -> bool:
        """Check if content is duplicate of existing section"""
        
        for existing_section in existing_sections.values():
            if len(content) > 50 and len(existing_section.content) > 50:
                # Check for significant overlap
                overlap = len(set(content.split()) & set(existing_section.content.split()))
                total_words = len(set(content.split()) | set(existing_section.content.split()))
                
                if total_words > 0 and overlap / total_words > 0.7:
                    return True
        
        return False
    
    def _adjust_confidence(self, section: Section) -> float:
        """Adjust confidence based on content quality"""
        
        confidence = section.confidence
        
        # Adjust based on content length
        if len(section.content) < 50:
            confidence -= 0.2
        elif len(section.content) > 500:
            confidence += 0.1
        
        # Adjust based on content structure
        lines = section.content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if len(non_empty_lines) < 2:
            confidence -= 0.3
        
        # Check for bullet points or structured content
        if any(line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')) for line in lines):
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def get_section_summary(self, sections: Dict[str, Section]) -> Dict:
        """Get summary of parsed sections"""
        
        return {
            "total_sections": len(sections),
            "sections": [
                {
                    "name": section.name,
                    "content_length": len(section.content),
                    "confidence": section.confidence,
                    "lines": section.end_line - section.start_line + 1
                }
                for section in sections.values()
            ],
            "coverage": self._calculate_coverage(sections)
        }
    
    def _calculate_coverage(self, sections: Dict[str, Section]) -> Dict[str, bool]:
        """Calculate which standard sections are present"""
        
        standard_sections = {
            'personal_info': ['persoonlijke_gegevens', 'personal_information'],
            'work_experience': ['werkervaring', 'work_experience'],
            'education': ['opleiding', 'education'],
            'skills': ['vaardigheden', 'skills'],
            'languages': ['talen', 'languages'],
            'software': ['software'],
            'certificates': ['certificaten', 'certificates'],
            'courses': ['cursussen', 'courses'],
            'projects': ['projecten', 'projects'],
            'profile': ['profiel', 'profile']
        }
        
        coverage = {}
        for category, section_names in standard_sections.items():
            coverage[category] = any(name in sections for name in section_names)
        
        return coverage
