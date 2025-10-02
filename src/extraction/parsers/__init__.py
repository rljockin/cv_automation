#!/usr/bin/env python3
"""
CV Parser - Parse extracted text into structured data
"""

import re
from typing import Dict, List, Optional
from src.core import CVData, PersonalInfo, WorkExperience, Education, Language, ExtractionResult
from .personal_info_parser import PersonalInfoParser

class CVParser:
    """Parse CV text into structured data"""
    
    def __init__(self):
        self.personal_info_parser = PersonalInfoParser()
    
    def parse_cv(self, extraction_result: ExtractionResult, filename: str = None):
        """Parse CV text into structured data"""
        try:
            if not extraction_result.success or not extraction_result.text:
                return {
                    'success': False,
                    'error': 'No text extracted from CV',
                    'confidence': 0.0
                }
            
            text = extraction_result.text
            language = self._detect_language(text)
            
            # Parse personal information (including filename-based name extraction)
            personal_info = self.personal_info_parser.parse_personal_info(text, language)
            
            # If no name found in document, try to extract from filename
            if not personal_info.full_name and filename:
                filename_name = self._extract_name_from_filename(filename)
                if filename_name:
                    personal_info.full_name = filename_name
                    first_name, last_name = self._extract_name_components(filename_name)
                    personal_info.first_name = first_name
                    personal_info.last_name = last_name
                    personal_info.confidence = max(personal_info.confidence, 0.8)  # High confidence for filename extraction
            
            # Parse work experience
            work_experience = self._parse_work_experience(text)
            
            # Parse education
            education = self._parse_education(text)
            
            # Parse skills
            skills = self._parse_skills(text)
            
            # Create CV data
            cv_data = CVData(
                cv_id=f"cv_{hash(text) % 100000:05d}",
                person_name=personal_info.full_name or "Unknown",
                personal_info=personal_info,
                work_experience=work_experience,
                education=education,
                skills=skills,
                language=language,
                source_file="cv_file",
                raw_text=text
            )
            
            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(personal_info, work_experience, education)
            
            return {
                'success': True,
                'cv_data': cv_data,
                'confidence': confidence
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'confidence': 0.0
            }
    
    def _detect_language(self, text: str) -> Language:
        """Detect the language of the CV text"""
        text_lower = text.lower()
        
        # Dutch keywords
        dutch_keywords = ['werkervaring', 'opleiding', 'vaardigheden', 'persoonlijk', 'geboren', 'woonplaats']
        dutch_count = sum(1 for keyword in dutch_keywords if keyword in text_lower)
        
        # English keywords
        english_keywords = ['work experience', 'education', 'skills', 'personal', 'born', 'residence']
        english_count = sum(1 for keyword in english_keywords if keyword in text_lower)
        
        if dutch_count > english_count:
            return Language.DUTCH
        elif english_count > dutch_count:
            return Language.ENGLISH
        else:
            return Language.UNKNOWN
    
    def _parse_work_experience(self, text: str) -> List[WorkExperience]:
        """Parse work experience from text"""
        work_experience = []
        
        # Look for work experience section
        work_section = self._extract_section(text, ['werkervaring', 'work experience', 'ervaring'])
        
        if work_section:
            # Simple parsing - look for company names and positions
            lines = work_section.split('\n')
            current_company = None
            current_position = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for company patterns
                if self._is_company_line(line):
                    if current_company and current_position:
                        work_exp = WorkExperience(
                            company=current_company,
                            position=current_position,
                            start_date=None,
                            end_date=None,
                            is_current=False,
                            location=None,
                            description="",
                            responsibilities=[],
                            projects=[],
                            technologies=[],
                            confidence=0.7
                        )
                        work_experience.append(work_exp)
                    
                    current_company = line
                    current_position = None
                elif self._is_position_line(line):
                    current_position = line
        
        return work_experience[:5]  # Limit to 5 most recent
    
    def _parse_education(self, text: str) -> List[Education]:
        """Parse education from text"""
        education = []
        
        # Look for education section
        edu_section = self._extract_section(text, ['opleiding', 'education', 'scholing'])
        
        if edu_section:
            lines = edu_section.split('\n')
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                
                # Look for degree patterns
                if self._is_education_line(line):
                    # Simple parsing - assume format is "Degree - Institution"
                    if ' - ' in line:
                        parts = line.split(' - ', 1)
                        degree = parts[0].strip()
                        institution = parts[1].strip()
                    else:
                        degree = line
                        institution = "Unknown Institution"
                    
                    edu = Education(
                        degree=degree,
                        institution=institution,
                        period=None,
                        graduation_year=None,
                        field_of_study=None
                    )
                    education.append(edu)
        
        return education[:3]  # Limit to 3 most recent
    
    def _parse_skills(self, text: str) -> List[str]:
        """Parse skills from text"""
        skills = []
        
        # Look for skills section
        skills_section = self._extract_section(text, ['vaardigheden', 'skills', 'competenties'])
        
        if skills_section:
            # Extract skills from text
            # Look for comma-separated lists or bullet points
            skill_text = skills_section.replace('\n', ' ').replace('•', ',').replace('-', ',')
            skill_items = [s.strip() for s in skill_text.split(',') if s.strip()]
            
            for skill in skill_items:
                if len(skill) > 2 and len(skill) < 50:  # Reasonable skill length
                    skills.append(skill)
        
        return skills[:15]  # Limit to 15 skills
    
    def _extract_section(self, text: str, section_names: List[str]) -> Optional[str]:
        """Extract a specific section from the CV text"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if this line is a section header
            for section_name in section_names:
                if section_name.lower() in line_lower:
                    # Found section header, extract content until next section
                    section_content = []
                    
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        
                        # Stop if we hit another section header
                        if self._is_section_header(next_line):
                            break
                        
                        if next_line:
                            section_content.append(next_line)
                    
                    return '\n'.join(section_content)
        
        return None
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is a section header"""
        if not line or len(line) < 3:
            return False
        
        # Common section headers
        section_headers = [
            'werkervaring', 'work experience', 'opleiding', 'education',
            'vaardigheden', 'skills', 'persoonlijk', 'personal',
            'projecten', 'projects', 'talen', 'languages',
            'certificaten', 'certificates', 'cursussen', 'courses'
        ]
        
        line_lower = line.lower()
        return any(header in line_lower for header in section_headers)
    
    def _is_company_line(self, line: str) -> bool:
        """Check if a line looks like a company name"""
        # Company names are usually short, contain letters, and don't start with common CV words
        if len(line) < 3 or len(line) > 50:
            return False
        
        # Skip lines that look like dates or positions
        if re.search(r'\d{4}', line) or any(word in line.lower() for word in ['bij', 'at', 'manager', 'developer']):
            return False
        
        return True
    
    def _is_position_line(self, line: str) -> bool:
        """Check if a line looks like a job position"""
        position_keywords = ['manager', 'developer', 'analyst', 'consultant', 'engineer', 'specialist']
        return any(keyword in line.lower() for keyword in position_keywords)
    
    def _is_education_line(self, line: str) -> bool:
        """Check if a line looks like an education entry"""
        education_keywords = ['bachelor', 'master', 'hbo', 'mbo', 'universiteit', 'university', 'college']
        return any(keyword in line.lower() for keyword in education_keywords)
    
    def _calculate_overall_confidence(self, personal_info, work_experience, education) -> float:
        """Calculate overall confidence score"""
        confidence = 0.0
        
        # Personal info confidence (40% weight)
        confidence += personal_info.confidence * 0.4
        
        # Work experience confidence (40% weight)
        if work_experience:
            confidence += 0.4
        else:
            confidence += 0.1
        
        # Education confidence (20% weight)
        if education:
            confidence += 0.2
        else:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _extract_name_from_filename(self, filename: str) -> Optional[str]:
        """Extract person name from filename"""
        if not filename:
            return None
        
        # Remove file extension
        name_part = filename.replace('.docx', '').replace('.pdf', '').replace('.doc', '')
        
        # Remove common CV prefixes
        prefixes = ['CV', 'cv', 'Resume', 'resume', 'Resumé', 'resumé']
        for prefix in prefixes:
            if name_part.startswith(prefix):
                name_part = name_part[len(prefix):].strip()
                break
        
        # Remove year patterns (e.g., "2025", "2024")
        import re
        name_part = re.sub(r'\s*\d{4}\s*$', '', name_part).strip()
        
        # Clean up name
        name_part = name_part.replace('_', ' ').replace('-', ' ').strip()
        
        # Validate that it looks like a name
        if self._is_likely_name(name_part):
            return name_part
        
        return None
    
    def _extract_name_components(self, full_name: str) -> tuple:
        """Extract first and last name from full name"""
        if not full_name:
            return None, None
        
        parts = full_name.split()
        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            # For names with multiple parts, first is first name, rest is last name
            return parts[0], ' '.join(parts[1:])
    
    def _is_likely_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        if not text or len(text) < 3 or len(text) > 50:
            return False
        
        # Should contain letters
        if not re.search(r'[A-Za-z]', text):
            return False
        
        # Should not contain numbers (except in rare cases)
        if re.search(r'\d', text):
            return False
        
        # Should not contain common CV words
        cv_words = ['cv', 'resume', 'curriculum', 'vitae', 'werkervaring', 'opleiding',
                   'vaardigheden', 'experience', 'education', 'skills']
        if any(word in text.lower() for word in cv_words):
            return False
        
        # Should not be all caps (unless it's a short name)
        if text.isupper() and len(text) > 10:
            return False
        
        # Should have reasonable word count
        words = text.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        return True

__all__ = ['CVParser']