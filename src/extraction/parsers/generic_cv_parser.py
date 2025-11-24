#!/usr/bin/env python3
"""
Generic CV Parser - Handles all CV formats found in Network Folder analysis
Based on comprehensive analysis of 949 CVs with 93.7% success rate
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, date
import logging

from src.core import CVData, PersonalInfo, WorkExperience, Education, Language, ExtractionResult
from src.core.logger import setup_logger, log_error_with_context


@dataclass
class ParsedSection:
    """Represents a parsed CV section"""
    name: str
    content: str
    start_line: int
    end_line: int
    confidence: float
    language: Language


class GenericCVParser:
    """
    Generic CV Parser that handles all CV formats found in Network Folder
    
    Based on analysis of 949 CVs:
    - 89.8% Dutch, 3.1% English, 0.3% Mixed
    - 49.7% DOCX, 44.5% PDF, 5.8% DOC
    - 93.7% successful text extraction
    - Handles various section patterns and date formats
    """
    
    def __init__(self):
        """Initialize parser with comprehensive patterns from analysis"""
        self.logger = setup_logger(__name__)
        
        # Section patterns from analysis (lines 118-180 in investigation summary)
        # Updated to handle common CV formats including all-caps headers
        self.section_patterns = {
            'personal_info': [
                r'(?i)^\s*(personalia|persoonlijke\s*gegevens|gegevens|personal\s*info|contact)\s*$',
                r'(?i)^\s*(personalia|persoonlijke\s*gegevens|gegevens|personal\s*info|contact)\s*:?\s*$'
            ],
            'profile': [
                r'(?i)^\s*(profiel|profile|samenvatting|summary|over\s*mij|about\s*me)\s*$',
                r'(?i)^\s*(profiel|profile|samenvatting|summary|over\s*mij|about\s*me)\s*:?\s*$'
            ],
            'work_experience': [
                r'(?i)^\s*(werkervaring|ervaring|work\s*experience|professional\s*experience|loopbaan|carrière)\s*$',
                r'(?i)^\s*(werkervaring|ervaring|work\s*experience|professional\s*experience|loopbaan|carrière)\s*:?\s*$',
                r'(?i)^\s*(werkervaring|ervaring|work\s*experience|professional\s*experience|loopbaan|carrière)\s+',  # Match at start of line
                r'(?i)^\s*(werkervaring|ervaring|work\s*experience|professional\s*experience|loopbaan|carrière)\s*$',  # Match entire line
                r'(?i)^\s*ERVARING\s*$',  # All caps variant
                r'(?i)^\s*WERKERVARING\s*$',  # All caps variant
                r'(?i)^\s*CAREER\s*$',  # All caps variant
                r'(?i)^\s*LOOPBAAN\s*$',  # All caps variant
            ],
            'education': [
                r'(?i)^\s*(opleiding|opleidingen|education|scholing|studie)\s*$',
                r'(?i)^\s*(opleiding|opleidingen|education|scholing|studie)\s*:?\s*$',
                r'(?i)^\s*(opleiding|opleidingen|education|scholing|studie)\s+',  # Match at start of line
                r'(?i)^\s*(opleiding|opleidingen|education|scholing|studie)\s*$'  # Match entire line
            ],
            'projects': [
                r'(?i)^\s*(projecten|projects|project\s*ervaring|uitgevoerde\s*projecten)\s*$',
                r'(?i)^\s*(projecten|projects|project\s*ervaring|uitgevoerde\s*projecten)\s*:?\s*$',
                r'(?i)^\s*(projecten|projects|project\s*ervaring|uitgevoerde\s*projecten)\s+',  # Match at start of line
                r'(?i)^\s*(projecten|projects|project\s*ervaring|uitgevoerde\s*projecten)\s*$'  # Match entire line
            ],
            'skills': [
                r'(?i)^\s*(vaardigheden|skills|competenties|competencies|kennis)\s*$',
                r'(?i)^\s*(vaardigheden|skills|competenties|competencies|kennis)\s*:?\s*$'
            ],
            'courses': [
                r'(?i)^\s*(cursussen|courses|training|opleidingen|studies)\s*$',
                r'(?i)^\s*(cursussen|courses|training|opleidingen|studies)\s*:?\s*$',
                r'(?i)^\s*(cursussen|courses|training|opleidingen|studies)\s+',  # Match at start of line
                r'(?i)^\s*(cursussen|courses|training|opleidingen|studies)\s*$'  # Match entire line
            ],
            'languages': [
                r'(?i)^\s*(talen|languages|talenkennis|language\s*skills)\s*$',
                r'(?i)^\s*(talen|languages|talenkennis|language\s*skills)\s*:?\s*$'
            ],
            'software': [
                r'(?i)^\s*(software|tools|applicaties|programma\'s|it\s*skills)\s*$',
                r'(?i)^\s*(software|tools|applicaties|programma\'s|it\s*skills)\s*:?\s*$',
                r'(?i)^\s*(software|tools|applicaties|programma\'s|it\s*skills)\s+',  # Match at start of line
                r'(?i)^\s*(software|tools|applicaties|programma\'s|it\s*skills)\s*$'  # Match entire line
            ],
            'certifications': [
                r'(?i)^\s*(certificaten|certificates|certificering|certifications)\s*$',
                r'(?i)^\s*(certificaten|certificates|certificering|certifications)\s*:?\s*$'
            ]
        }
        
        # Date patterns from analysis (lines 100-112)
        self.date_patterns = [
            r'\b(19\d{2}|20[0-2]\d)\b',  # YYYY (93.2% usage)
            r'\b(19\d{2}|20[0-2]\d)\s*[-–]\s*(19\d{2}|20[0-2]\d|heden|present|now)\b',  # YYYY - YYYY (82.9%)
            r'\b(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(19\d{2}|20[0-2]\d)\b',  # Month YYYY (53.3%)
            r'\b\d{2}-\d{2}-(19\d{2}|20[0-2]\d)\b',  # DD-MM-YYYY (20.7%)
            r'\b\d{2}/(19\d{2}|20[0-2]\d)\b',  # MM/YYYY (11.7%)
        ]
        
        # Language detection keywords from analysis (lines 327-330)
        self.dutch_keywords = [
            'werkervaring', 'opleiding', 'vaardigheden', 'persoonlijk', 'projecten',
            'ervaring', 'scholing', 'competenties', 'talen', 'software', 'certificaten',
            'cursussen', 'personalia', 'profiel', 'geboren', 'woonplaats'
        ]
        
        self.english_keywords = [
            'work experience', 'education', 'skills', 'personal', 'projects',
            'experience', 'training', 'competencies', 'languages', 'software',
            'certificates', 'courses', 'personal info', 'profile', 'born', 'residence'
        ]
        
        # Common job title patterns
        self.job_title_patterns = [
            r'(?i)\b(engineer|ingenieur|manager|beheerder|consultant|adviseur|coördinator|coordinator|specialist|analist|developer|ontwikkelaar|architect|project\s*manager|team\s*lead|senior|junior|medior)\b',
            r'(?i)\b(director|directeur|ceo|cto|cfo|hoofd|head|leidinggevende|supervisor|supervisor)\b',
            r'(?i)\b(technician|technicus|operator|operator|assistant|assistent|secretary|secretaresse)\b'
        ]
        
        # Company name patterns
        self.company_patterns = [
            r'(?i)\b(bv|nv|bvba|nvba|bv\.|nv\.|ltd|inc|corp|corporation|company|bedrijf|onderneming)\b',
            r'(?i)\b(group|groep|holding|consultancy|consulting|engineering|techniek|services|diensten)\b'
        ]
    
    def parse_cv(self, extraction_result: ExtractionResult, filename: str = None) -> Dict[str, Any]:
        """
        Parse CV text into structured data using generic patterns
        
        Args:
            extraction_result: Result from text extraction
            filename: Original filename for name extraction fallback
            
        Returns:
            Dictionary with parsing results
        """
        try:
            if not extraction_result.success or not extraction_result.text:
                return {
                    'success': False,
                    'error': 'No text extracted from CV',
                    'confidence': 0.0
                }
            
            text = extraction_result.text
            language = self._detect_language(text)
            
            # Parse sections using generic patterns
            sections = self._parse_sections(text, language)
            
            # Extract structured data from sections
            personal_info = self._extract_personal_info(sections, text, filename)
            work_experience = self._extract_work_experience(sections, text)
            education = self._extract_education(sections, text)
            skills = self._extract_skills(sections, text)
            
            # Create CV data object
            cv_data = CVData(
                cv_id=f"cv_{hash(text) % 100000:05d}",
                person_name=personal_info.full_name or "Unknown",
                personal_info=personal_info,
                work_experience=work_experience,
                education=education,
                skills=skills,
                language=language,
                source_file=filename or "unknown",
                raw_text=text
            )
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(personal_info, work_experience, education, sections)
            
            return {
                'success': True,
                'cv_data': cv_data,
                'confidence': confidence,
                'sections_found': len(sections),
                'language': language.value
            }
            
        except Exception as e:
            log_error_with_context(
                self.logger,
                f"CV parsing failed for {filename}",
                e,
                {'text_length': len(extraction_result.text) if extraction_result.text else 0}
            )
            return {
                'success': False,
                'error': str(e),
                'confidence': 0.0
            }
    
    def _detect_language(self, text: str) -> Language:
        """Detect language using comprehensive keyword analysis"""
        text_lower = text.lower()
        
        dutch_count = sum(1 for keyword in self.dutch_keywords if keyword in text_lower)
        english_count = sum(1 for keyword in self.english_keywords if keyword in text_lower)
        
        if dutch_count > english_count:
            return Language.DUTCH
        elif english_count > dutch_count:
            return Language.ENGLISH
        else:
            return Language.UNKNOWN
    
    def _parse_sections(self, text: str, language: Language) -> Dict[str, ParsedSection]:
        """Parse CV into sections using comprehensive patterns"""
        sections = {}
        lines = text.split('\n')
        
        # Find all section headers
        section_headers = []
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 3:
                continue
            
            # Check against all section patterns
            for section_name, patterns in self.section_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, line_clean):
                        confidence = self._calculate_header_confidence(line_clean, pattern)
                        section_headers.append((i, section_name, confidence))
                        break
        
        # Sort by line number
        section_headers.sort(key=lambda x: x[0])
        
        # Extract section content
        for i, (line_num, section_name, confidence) in enumerate(section_headers):
            # Determine end line
            if i + 1 < len(section_headers):
                end_line = section_headers[i + 1][0] - 1
            else:
                end_line = len(lines) - 1
            
            # Extract content
            content_lines = lines[line_num + 1:end_line + 1]
            content = '\n'.join(content_lines).strip()
            
            # Skip empty sections
            if not content or len(content) < 10:
                continue
            
            section = ParsedSection(
                name=section_name,
                content=content,
                start_line=line_num,
                end_line=end_line,
                confidence=confidence,
                language=language
            )
            
            sections[section_name] = section
        
        return sections
    
    def _calculate_header_confidence(self, line: str, pattern: str) -> float:
        """Calculate confidence score for section header"""
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
    
    def _extract_personal_info(self, sections: Dict[str, ParsedSection], text: str, filename: str) -> PersonalInfo:
        """Extract personal information using multiple strategies"""
        
        # Strategy 1: Look for personal info section
        personal_section = sections.get('personal_info')
        if personal_section:
            return self._parse_personal_section(personal_section.content)
        
        # Strategy 2: Extract from document header (first few lines)
        header_text = '\n'.join(text.split('\n')[:10])
        personal_info = self._parse_personal_section(header_text)
        
        # Strategy 3: Extract name from filename if not found
        if not personal_info.full_name and filename:
            filename_name = self._extract_name_from_filename(filename)
            if filename_name:
                personal_info.full_name = filename_name
                first_name, last_name = self._extract_name_components(filename_name)
                personal_info.first_name = first_name
                personal_info.last_name = last_name
                personal_info.confidence = max(personal_info.confidence, 0.8)
        
        return personal_info
    
    def _parse_personal_section(self, text: str) -> PersonalInfo:
        """Parse personal information from text"""
        
        # Extract name (first non-empty line that looks like a name)
        lines = text.split('\n')
        full_name = None
        
        for line in lines:
            line = line.strip()
            if self._is_likely_name(line):
                full_name = line
                break
        
        # Extract other information using patterns
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        location = self._extract_location(text)
        birth_year = self._extract_birth_year(text)
        
        # Calculate confidence
        confidence = 0.0
        if full_name:
            confidence += 0.4
        if email:
            confidence += 0.2
        if phone:
            confidence += 0.2
        if location:
            confidence += 0.1
        if birth_year:
            confidence += 0.1
        
        first_name, last_name = self._extract_name_components(full_name) if full_name else (None, None)
        
        return PersonalInfo(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            location=location,
            birth_year=birth_year,
            phone=phone,
            email=email,
            website=None,
            nationality=None,
            driver_license=None,
            address=None,
            postal_code=None,
            city=location,
            confidence=confidence,
            language=Language.UNKNOWN
        )
    
    def _extract_work_experience(self, sections: Dict[str, ParsedSection], text: str) -> List[WorkExperience]:
        """Extract work experience using multiple strategies"""
        work_experience = []
        
        # Strategy 1: Parse work experience section
        work_section = sections.get('work_experience')
        if work_section:
            work_experience.extend(self._parse_work_section(work_section.content))
        
        # Strategy 2: Parse projects section for work experience
        projects_section = sections.get('projects')
        if projects_section:
            work_experience.extend(self._parse_projects_as_work(projects_section.content))
        
        # Strategy 3: Parse entire text for job patterns if no clear section
        if not work_experience:
            work_experience.extend(self._parse_job_patterns_from_text(text))
        
        # Strategy 4: Direct parsing from text using improved patterns
        if not work_experience:
            work_experience.extend(self._parse_work_experience_direct(text))
        
        # Remove duplicates and limit
        unique_work = []
        seen_companies = set()
        for work in work_experience:
            if work.company and work.company not in seen_companies:
                unique_work.append(work)
                seen_companies.add(work.company)
        
        self.logger.debug(f"Extracted {len(unique_work)} work experiences")
        return unique_work[:20]  # Increased limit to capture more entries
    
    def _parse_work_experience_direct(self, text: str) -> List[WorkExperience]:
        """Direct parsing of work experience from text using improved patterns"""
        work_experience = []
        
        # Look for "ERVARING" section specifically
        ervaring_start = text.find("ERVARING")
        if ervaring_start != -1:
            # Find the end of the ERVARING section (next major section)
            next_sections = ["PROJECTEN", "OPLEIDINGEN", "CURSUSSEN", "SOFTWARE"]
            ervaring_end = len(text)
            
            for section in next_sections:
                section_pos = text.find(section, ervaring_start + 1)
                if section_pos != -1 and section_pos < ervaring_end:
                    ervaring_end = section_pos
            
            ervaring_content = text[ervaring_start:ervaring_end]
            
            # Parse job entries from ERVARING content
            lines = ervaring_content.split('\n')
            current_job = None
            
            for line in lines:
                line = line.strip()
                if not line or line == "ERVARING":
                    continue
                
                # Look for job title patterns
                if any(keyword in line.lower() for keyword in ['adviseur', 'manager', 'engineer', 'consultant', 'specialist', 'coördinator']):
                    if current_job:
                        work_experience.append(current_job)
                    
                    # Extract job title and company
                    if ' - ' in line:
                        parts = line.split(' - ', 1)
                        position = parts[0].strip()
                        company = parts[1].strip()
                    else:
                        position = line
                        company = "Unknown Company"
                    
                    current_job = WorkExperience(
                        company=company,
                        position=position,
                        start_date=None,
                        end_date=None,
                        is_current=False,
                        location=None,
                        description="",
                        responsibilities=[],
                        projects=[],
                        technologies=[],
                        confidence=0.8
                    )
                
                # Look for date patterns - improved regex
                elif re.search(r'\d{4}', line) and ('heden' in line.lower() or 'present' in line.lower() or 'nu' in line.lower() or ' - ' in line or '–' in line or '—' in line):
                    if current_job:
                        current_job.is_current = any(word in line.lower() for word in ['heden', 'present', 'nu'])
                        # Extract dates with better regex - handles different dash types
                        date_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4}|heden|present|nu)', line, re.IGNORECASE)
                        if date_match:
                            current_job.start_date = date_match.group(1)
                            end_date_text = date_match.group(2).lower()
                            if end_date_text not in ['heden', 'present', 'nu']:
                                current_job.end_date = date_match.group(2)
            
            if current_job:
                work_experience.append(current_job)
        
        return work_experience
    
    def _parse_work_section(self, content: str) -> List[WorkExperience]:
        """Parse work experience from section content"""
        work_experience = []
        lines = content.split('\n')
        
        current_job = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for job patterns
            if self._is_job_line(line):
                if current_job:
                    work_experience.append(current_job)
                
                current_job = self._parse_job_line(line)
            elif current_job and line:
                # Add description or responsibilities
                if not current_job.description:
                    current_job.description = line
                else:
                    current_job.description += f" {line}"
        
        if current_job:
            work_experience.append(current_job)
        
        return work_experience
    
    def _parse_projects_as_work(self, content: str) -> List[WorkExperience]:
        """Parse projects section as work experience"""
        work_experience = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for project patterns that could be work experience
            if '|' in line and any(keyword in line.lower() for keyword in ['project', 'opdracht', 'werkzaamheden']):
                work_exp = self._parse_job_line(line)
                if work_exp:
                    work_experience.append(work_exp)
        
        return work_experience
    
    def _parse_job_patterns_from_text(self, text: str) -> List[WorkExperience]:
        """Parse job patterns from entire text when no clear section exists"""
        work_experience = []
        
        # Look for common job patterns
        job_patterns = [
            r'([^|]+)\s*\|\s*([^|]+)\s+([^|]+?)\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december|\d{4})\s+(\d{4}|heden)',
            r'([^|]+)\s*\|\s*([^|]+)\s+([^|]+?)\s+(\d{4})\s*[-–]\s*(\d{4}|heden)',
            r'([A-Za-z\s]+)\s*\|\s*([A-Za-z\s&]+)\s+([^|]+?)\s+(\d{4})\s*[-–]\s*(\d{4}|heden)'
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 5:
                    position = groups[0].strip()
                    company = groups[1].strip()
                    
                    # Skip if looks like section header
                    if any(word in position.lower() for word in ['werkervaring', 'opleiding', 'vaardigheden']):
                        continue
                    
                    # Skip if too short
                    if len(position) < 3 or len(company) < 3:
                        continue
                    
                    work_exp = WorkExperience(
                        company=company,
                        position=position,
                        start_date=None,
                        end_date=None,
                        is_current='heden' in groups[-1].lower(),
                        location=None,
                        description="",
                        responsibilities=[],
                        projects=[],
                        technologies=[],
                        confidence=0.7
                    )
                    work_experience.append(work_exp)
        
        return work_experience
    
    def _is_job_line(self, line: str) -> bool:
        """Check if line looks like a job entry"""
        # Look for job title patterns
        for pattern in self.job_title_patterns:
            if re.search(pattern, line):
                return True
        
        # Look for company patterns
        for pattern in self.company_patterns:
            if re.search(pattern, line):
                return True
        
        # Look for date patterns
        for pattern in self.date_patterns:
            if re.search(pattern, line):
                return True
        
        return False
    
    def _parse_job_line(self, line: str) -> Optional[WorkExperience]:
        """Parse a single job line into WorkExperience object"""
        try:
            # Try to split by common separators
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    position = parts[0].strip()
                    company = parts[1].strip()
                    
                    # Extract dates if present
                    date_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|heden)', line)
                    is_current = 'heden' in line.lower()
                    
                    return WorkExperience(
                        company=company,
                        position=position,
                        start_date=None,
                        end_date=None,
                        is_current=is_current,
                        location=None,
                        description="",
                        responsibilities=[],
                        projects=[],
                        technologies=[],
                        confidence=0.6
                    )
        except:
            pass
        
        return None
    
    def _extract_education(self, sections: Dict[str, ParsedSection], text: str) -> List[Education]:
        """Extract education information"""
        education = []
        
        # Strategy 1: Parse education section
        edu_section = sections.get('education')
        if edu_section:
            education.extend(self._parse_education_section(edu_section.content))
        
        # Strategy 2: Parse courses section for education
        courses_section = sections.get('courses')
        if courses_section:
            education.extend(self._parse_courses_as_education(courses_section.content))
        
        # Strategy 3: Parse entire text for education patterns
        if not education:
            education.extend(self._parse_education_patterns_from_text(text))
        
        # Strategy 4: Direct parsing from text using improved patterns
        if not education:
            education.extend(self._parse_education_direct(text))
        
        return education[:3]  # Limit to 3 most recent
    
    def _parse_education_direct(self, text: str) -> List[Education]:
        """Direct parsing of education from text using improved patterns"""
        education = []
        
        # Look for "OPLEIDINGEN" section specifically
        opleidingen_start = text.find("OPLEIDINGEN")
        if opleidingen_start != -1:
            # Find the end of the OPLEIDINGEN section (next major section)
            next_sections = ["CURSUSSEN", "SOFTWARE", "PROJECTEN"]
            opleidingen_end = len(text)
            
            for section in next_sections:
                section_pos = text.find(section, opleidingen_start + 1)
                if section_pos != -1 and section_pos < opleidingen_end:
                    opleidingen_end = section_pos
            
            opleidingen_content = text[opleidingen_start:opleidingen_end]
            
            # Parse education entries from OPLEIDINGEN content
            lines = opleidingen_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line == "OPLEIDINGEN":
                    continue
                
                # Look for education patterns: "YYYY-YYYY: Degree, Institution"
                if re.search(r'\d{4}', line) and ':' in line:
                    # Split by colon
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        period = parts[0].strip()
                        degree_institution = parts[1].strip()
                        
                        # Split degree and institution by comma
                        if ',' in degree_institution:
                            degree_parts = degree_institution.split(',', 1)
                            degree = degree_parts[0].strip()
                            institution = degree_parts[1].strip()
                        else:
                            degree = degree_institution
                            institution = "Unknown Institution"
                        
                        edu = Education(
                            degree=degree,
                            institution=institution,
                            period=period,
                            graduation_year=None,
                            field_of_study=None
                        )
                        education.append(edu)
        
        return education
    
    def _parse_education_section(self, content: str) -> List[Education]:
        """Parse education from section content"""
        education = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Look for education patterns
            if self._is_education_line(line):
                edu = self._parse_education_line(line)
                if edu:
                    education.append(edu)
        
        return education
    
    def _parse_courses_as_education(self, content: str) -> List[Education]:
        """Parse courses section as education"""
        education = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for course patterns that could be education
            if any(keyword in line.lower() for keyword in ['bachelor', 'master', 'hbo', 'mbo', 'universiteit', 'hogeschool', 'college']):
                edu = self._parse_education_line(line)
                if edu:
                    education.append(edu)
        
        return education
    
    def _parse_education_patterns_from_text(self, text: str) -> List[Education]:
        """Parse education patterns from entire text"""
        education = []
        
        # Look for education patterns
        edu_patterns = [
            r'([^|]+)\s*\|\s*([^|]+)\s+([^|]+?)\s+(september|januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december|\d{4})\s+(\d{4}|heden)',
            r'([^|]+)\s*\|\s*([^|]+)\s+([^|]+?)\s+(\d{4})\s*[-–]\s*(\d{4}|heden)',
        ]
        
        for pattern in edu_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 5:
                    degree = groups[0].strip()
                    institution = groups[1].strip()
                    
                    # Skip if looks like work experience
                    if any(word in degree.lower() for word in ['engineer', 'manager', 'consultant', 'coördinator']):
                        continue
                    
                    # Look for education keywords
                    if any(keyword in degree.lower() for keyword in ['bachelor', 'master', 'hbo', 'mbo', 'universiteit', 'hogeschool', 'college']):
                        if len(degree) > 3 and len(institution) > 3:
                            edu = Education(
                                degree=degree,
                                institution=institution,
                                period=None,
                                graduation_year=None,
                                field_of_study=None
                            )
                            education.append(edu)
        
        return education
    
    def _is_education_line(self, line: str) -> bool:
        """Check if line looks like an education entry"""
        education_keywords = [
            'bachelor', 'master', 'hbo', 'mbo', 'universiteit', 'university', 
            'college', 'hogeschool', 'studie', 'diploma', 'certificaat'
        ]
        return any(keyword in line.lower() for keyword in education_keywords)
    
    def _parse_education_line(self, line: str) -> Optional[Education]:
        """Parse a single education line"""
        try:
            # Try to split by common separators
            if ' - ' in line:
                parts = line.split(' - ', 1)
                degree = parts[0].strip()
                institution = parts[1].strip()
            elif '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    degree = parts[0].strip()
                    institution = parts[1].strip()
                else:
                    return None
            else:
                degree = line
                institution = "Unknown Institution"
            
            return Education(
                degree=degree,
                institution=institution,
                period=None,
                graduation_year=None,
                field_of_study=None
            )
        except:
            return None
    
    def _extract_skills(self, sections: Dict[str, ParsedSection], text: str) -> List[str]:
        """Extract skills using multiple strategies"""
        skills = []
        
        # Strategy 1: Parse skills section
        skills_section = sections.get('skills')
        if skills_section:
            skills.extend(self._parse_skills_section(skills_section.content))
        
        # Strategy 2: Parse software section
        software_section = sections.get('software')
        if software_section:
            skills.extend(self._parse_skills_section(software_section.content))
        
        # Strategy 3: Direct parsing from SOFTWARE section (try this first)
        skills.extend(self._parse_software_skills_direct(text))
        
        # Strategy 4: Extract from entire text (only if no software skills found)
        if not skills:
            skills.extend(self._extract_skills_from_text(text))
        
        # Remove duplicates and limit
        unique_skills = list(dict.fromkeys(skills))  # Remove duplicates while preserving order
        return unique_skills[:15]  # Limit to 15 skills
    
    def _parse_software_skills_direct(self, text: str) -> List[str]:
        """Direct parsing of software skills from SOFTWARE section"""
        skills = []
        
        # Look for "SOFTWARE" section specifically
        software_start = text.find("SOFTWARE")
        if software_start != -1:
            # Find the end of the SOFTWARE section (end of text or next major section)
            software_end = len(text)
            
            # Get the SOFTWARE section content
            software_content = text[software_start:software_end]
            
            # Parse software skills from the content
            # Pattern: "Software Name: level" or "Software Name: level. Software Name: level"
            lines = software_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line == "SOFTWARE":
                    continue
                
                # Split by periods to get individual software entries
                software_entries = line.split('.')
                
                for entry in software_entries:
                    entry = entry.strip()
                    if ':' in entry:
                        # Split by colon to get software name and level
                        parts = entry.split(':', 1)
                        if len(parts) == 2:
                            software_name = parts[0].strip()
                            level = parts[1].strip()
                            
                            # Clean up software name
                            software_name = software_name.replace('MS-', 'MS ')
                            software_name = software_name.replace('MS ', 'Microsoft ')
                            
                            if software_name and len(software_name) > 1:
                                skills.append(software_name)
        
        return skills
    
    def _parse_skills_section(self, content: str) -> List[str]:
        """Parse skills from section content"""
        skills = []
        
        # Look for skills patterns
        skill_patterns = [
            r'([A-Za-z\s&]+)\s*\|\s*([A-Za-z\s&]+)',  # Pipe-separated skills
            r'([A-Za-z\s&]+),\s*([A-Za-z\s&]+)',     # Comma-separated skills
            r'•\s*([A-Za-z\s&]+)',                    # Bullet point skills
            r'-\s*([A-Za-z\s&]+)',                    # Dash-separated skills
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                for group in groups:
                    if group:
                        skill = group.strip()
                        skill = re.sub(r'\s+', ' ', skill)
                        
                        # Skip if too short or looks like a section header
                        if len(skill) < 3 or len(skill) > 50:
                            continue
                        
                        # Skip if looks like a section header
                        if any(word in skill.lower() for word in ['werkervaring', 'opleiding', 'vaardigheden', 'skills']):
                            continue
                        
                        # Skip if looks like a job title
                        if any(word in skill.lower() for word in ['engineer', 'manager', 'consultant', 'coördinator', 'director']):
                            continue
                        
                        skills.append(skill)
        
        return skills
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from entire text using keyword matching"""
        skills = []
        
        # Common skill keywords
        skill_keywords = [
            'maintenance', 'asset management', 'project management', 'lean', 'six sigma',
            'maximo', 'ultimo', 'excel', 'word', 'sharepoint', 'vca', 'iso9001', 'iso14001',
            'systems engineering', 'drone', 'wordpress', 'web development', 'cnc', 'cad',
            'quality management', 'process optimization', 'supply chain', 'change management',
            'human resource', 'strategy', 'it', 'mechanical engineering', 'industrial engineering',
            'python', 'java', 'javascript', 'sql', 'oracle', 'sap', 'autocad', 'solidworks'
        ]
        
        text_lower = text.lower()
        for keyword in skill_keywords:
            if keyword in text_lower and keyword.title() not in skills:
                skills.append(keyword.title())
        
        return skills
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        patterns = [
            r'\b(?:\+31\s?)?(?:0\s?)?[1-9]\d{1,2}[- ]?\d{6,7}\b',  # Dutch format
            r'\b\+?\d{1,3}[- ]?\d{2,4}[- ]?\d{2,4}[- ]?\d{2,4}\b'   # International format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location information"""
        # Dutch cities
        dutch_cities = [
            'amsterdam', 'rotterdam', 'den haag', 'utrecht', 'eindhoven', 'tilburg',
            'groningen', 'almere', 'breda', 'nijmegen', 'enschede', 'haarlem',
            'arnhem', 'zaandam', 'amersfoort', 'apeldoorn', 'hoofddorp', 'maastricht'
        ]
        
        text_lower = text.lower()
        for city in dutch_cities:
            if city in text_lower:
                return city.title()
        
        return None
    
    def _extract_birth_year(self, text: str) -> Optional[int]:
        """Extract birth year"""
        # Multiple patterns to catch different formats
        patterns = [
            r'\b(?:geboren|born|geboortedatum|birth\s*date|geb\.|b\.)\s*:?\s*(?:in\s*)?(19\d{2}|20[0-1]\d)\b',
            r'geboortedatum\s*:\s*\d{1,2}-\d{1,2}-(\d{4})',  # 16-07-1986 format
            r'(\d{4})-\d{1,2}-\d{1,2}',  # 1986-07-16 format
            r'\d{1,2}-\d{1,2}-(\d{4})',  # 16-07-1986 format
            r'(\d{4})\s*geboren'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    year = int(match.group(1))
                    if 1920 <= year <= 2010:
                        return year
                except (ValueError, TypeError):
                    pass
        
        return None
    
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
        
        # Remove year patterns
        name_part = re.sub(r'\s*\d{4}\s*$', '', name_part).strip()
        
        # Clean up name
        name_part = name_part.replace('_', ' ').replace('-', ' ').strip()
        
        # Validate that it looks like a name
        if self._is_likely_name(name_part):
            return name_part
        
        return None
    
    def _extract_name_components(self, full_name: str) -> Tuple[Optional[str], Optional[str]]:
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
    
    def _calculate_confidence(self, personal_info: PersonalInfo, work_experience: List[WorkExperience], 
                            education: List[Education], sections: Dict[str, ParsedSection]) -> float:
        """Calculate overall confidence score"""
        confidence = 0.0
        
        # Personal info confidence (30% weight)
        confidence += personal_info.confidence * 0.3
        
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
        
        # Sections found confidence (10% weight)
        if len(sections) >= 3:
            confidence += 0.1
        elif len(sections) >= 1:
            confidence += 0.05
        
        return min(confidence, 1.0)


__all__ = ['GenericCVParser', 'ParsedSection']
