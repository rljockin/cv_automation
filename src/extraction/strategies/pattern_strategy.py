#!/usr/bin/env python3
"""
Pattern-Based Parsing Strategy
Fast, free, uses comprehensive pattern libraries from 949 CV analysis
Target: 70% success rate, < 1 second per CV
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from src.core.logger import setup_logger

class PatternStrategy:
    """
    Pattern-based CV parsing using comprehensive pattern libraries
    Generic approach using data-driven patterns from 949 CV analysis
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing PatternStrategy...")
        
        # Load pattern libraries
        self._load_patterns()
        
        self.logger.info("PatternStrategy initialized with comprehensive patterns")
    
    def _load_patterns(self):
        """Load all pattern libraries"""
        patterns_dir = Path("src/extraction/patterns")
        
        # Load section patterns
        with open(patterns_dir / "section_patterns.json", 'r', encoding='utf-8') as f:
            self.section_patterns = json.load(f)
        
        # Load date patterns
        with open(patterns_dir / "date_patterns.json", 'r', encoding='utf-8') as f:
            self.date_patterns = json.load(f)
        
        # Load name patterns
        with open(patterns_dir / "name_patterns.json", 'r', encoding='utf-8') as f:
            self.name_patterns = json.load(f)
        
        # Load work patterns
        with open(patterns_dir / "work_patterns.json", 'r', encoding='utf-8') as f:
            self.work_patterns = json.load(f)
        
        self.logger.info(f"Loaded patterns: {len(self.section_patterns)} section types, "
                        f"{len(self.date_patterns['formats'])} date formats")
    
    def parse(self, cv_text: str, filename: str) -> Dict:
        """
        Parse CV using pattern-based extraction
        
        Args:
            cv_text: Full CV text
            filename: Original filename for fallback name extraction
            
        Returns:
            Dictionary with extracted data
        """
        self.logger.info(f"Starting pattern-based parsing for {filename}")
        
        try:
            # Detect language
            language = self._detect_language(cv_text)
            self.logger.debug(f"Detected language: {language}")
            
            # Detect sections
            sections = self._detect_sections(cv_text)
            self.logger.debug(f"Detected {len(sections)} sections")
            
            # Extract data from sections
            personal_info = self._extract_personal_info(sections, cv_text, filename)
            work_experience = self._extract_work_experience(sections, cv_text)
            education = self._extract_education(sections, cv_text)
            skills = self._extract_skills(sections, cv_text)
            languages_found = self._extract_languages(sections, cv_text)
            courses = self._extract_courses(sections, cv_text)
            profile = self._extract_profile(sections, cv_text)
            
            # Build result
            result = {
                'personal_info': personal_info,
                'work_experience': work_experience,
                'education': education,
                'courses': courses,
                'skills': skills,
                'languages': languages_found,
                'certifications': [],
                'profile_summary': profile,
                'confidence_score': 0.7  # Default for pattern-based
            }
            
            self.logger.info(f"Pattern parsing complete: {len(work_experience)} work entries, {len(education)} education entries")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pattern parsing failed: {str(e)}", exc_info=True)
            return self._empty_result()
    
    def _detect_language(self, text: str) -> str:
        """Detect CV language (Dutch or English)"""
        dutch_keywords = ['werkervaring', 'opleiding', 'vaardigheden', 'profiel', 'cursussen']
        english_keywords = ['experience', 'education', 'skills', 'profile', 'courses']
        
        text_lower = text.lower()
        dutch_count = sum(1 for kw in dutch_keywords if kw in text_lower)
        english_count = sum(1 for kw in english_keywords if kw in text_lower)
        
        return 'Dutch' if dutch_count > english_count else 'English'
    
    def _detect_sections(self, text: str) -> Dict[str, Tuple[int, int, str]]:
        """
        Detect all CV sections using pattern library
        
        Returns:
            Dict of {section_type: (start_line, end_line, content)}
        """
        sections = {}
        lines = text.split('\n')
        
        # Find section headers
        for section_type, patterns in self.section_patterns.items():
            regex_patterns = patterns.get('regex_patterns', [])
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Try each regex pattern
                for pattern in regex_patterns:
                    try:
                        if re.match(pattern, line_clean, re.IGNORECASE):
                            sections[section_type] = (i, i, line_clean)
                            break
                    except:
                        continue
        
        return sections
    
    def _extract_personal_info(self, sections: Dict, text: str, filename: str) -> Dict:
        """Extract personal information using multiple strategies"""
        personal_info = {
            'full_name': None,
            'first_name': None,
            'last_name': None,
            'location': None,
            'birth_year': None,
            'phone': None,
            'email': None
        }
        
        # Strategy 1: Extract from filename
        name_from_file = self._extract_name_from_filename(filename)
        if name_from_file and self._is_valid_name(name_from_file):
            personal_info['full_name'] = name_from_file
            parts = name_from_file.split()
            if len(parts) >= 2:
                personal_info['first_name'] = parts[0]
                personal_info['last_name'] = ' '.join(parts[1:])
        
        # Strategy 2: Extract from first lines
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line_clean = line.strip()
            if self._is_valid_name(line_clean) and len(line_clean) < 50:
                personal_info['full_name'] = line_clean
                break
        
        # Extract birth year
        birth_year = self._extract_birth_year(text)
        if birth_year:
            personal_info['birth_year'] = birth_year
        
        # Extract location
        location = self._extract_location(text)
        if location:
            personal_info['location'] = location
        
        return personal_info
    
    def _extract_work_experience(self, sections: Dict, text: str) -> List[Dict]:
        """
        Extract work experience from ALL relevant sections
        Handles multi-section CVs (Ervaring + Projecten, Loopbaan + Relevante werkervaring, etc.)
        """
        all_work_experience = []
        
        # Define work-related section types (GENERIC)
        work_section_types = ['Work Experience', 'Projects', 'Career']
        
        # Extract from each detected work-related section
        for section_type in work_section_types:
            if section_type in sections:
                self.logger.debug(f"Extracting work experience from section: {section_type}")
                entries = self._extract_from_work_section(section_type, sections, text)
                all_work_experience.extend(entries)
        
        # Also scan full text for work entries with keywords (fallback)
        if len(all_work_experience) < 5:  # If we didn't find much, try full text scan
            self.logger.debug("Scanning full text for additional work entries")
            keyword_entries = self._extract_work_by_keywords(text)
            all_work_experience.extend(keyword_entries)
        
        # Deduplicate and sort by date
        unique_work = self._deduplicate_work_experience(all_work_experience)
        
        self.logger.info(f"Extracted {len(unique_work)} unique work experience entries from {len(work_section_types)} section types")
        
        # Limit to reasonable number (increased from 20 to 50 for multi-section support)
        return unique_work[:50]
    
    def _extract_from_work_section(self, section_type: str, sections: Dict, text: str) -> List[Dict]:
        """Extract work entries from a specific section"""
        work_entries = []
        work_text = text  # Will be refined if section is detected
        
        # Extract using date patterns as anchors
        for date_pattern in self.date_patterns['formats'][:3]:  # Top 3 patterns
            pattern = date_pattern['pattern']
            matches = re.finditer(pattern, work_text, re.IGNORECASE)
            
            for match in matches:
                # Found a date, extract surrounding context
                start = max(0, match.start() - 100)
                end = min(len(work_text), match.end() + 200)
                context = work_text[start:end]
                
                # Extract work entry from context
                work_entry = self._parse_work_context(context, match.group(0))
                if work_entry:
                    work_entries.append(work_entry)
        
        return work_entries
    
    def _extract_work_by_keywords(self, text: str) -> List[Dict]:
        """
        Scan full text for work entries using keywords
        Fallback method when section detection doesn't work
        """
        work_entries = []
        lines = text.split('\n')
        
        # Look for lines with work-related keywords + dates
        for i, line in enumerate(lines):
            # Check if line has both a date and work-related content
            has_date = any(re.search(p['pattern'], line, re.IGNORECASE) for p in self.date_patterns['formats'][:3])
            has_work_keyword = any(kw in line.lower() for kw in ['project', 'manager', 'engineer', 'coordinator', 'consultant'])
            
            if has_date and (has_work_keyword or len(line) > 30):
                # Extract context around this line
                start_line = max(0, i - 2)
                end_line = min(len(lines), i + 5)
                context = '\n'.join(lines[start_line:end_line])
                
                # Try to parse as work entry
                for date_pattern in self.date_patterns['formats'][:3]:
                    match = re.search(date_pattern['pattern'], line, re.IGNORECASE)
                    if match:
                        work_entry = self._parse_work_context(context, match.group(0))
                        if work_entry:
                            work_entries.append(work_entry)
                        break
        
        return work_entries
    
    def _deduplicate_work_experience(self, work_list: List[Dict]) -> List[Dict]:
        """
        Remove duplicate work entries based on company, position, and dates
        Generic deduplication logic
        """
        seen = set()
        unique = []
        
        for work in work_list:
            # Create unique key
            company = work.get('company', '').lower().strip()
            position = work.get('position', '').lower().strip()
            start_date = work.get('start_date', '').strip()
            
            key = f"{company}|{position}|{start_date}"
            
            if key not in seen and (company or position):  # At least one should be present
                seen.add(key)
                unique.append(work)
        
        # Sort by start_date (most recent first)
        sorted_work = sorted(unique, key=lambda x: x.get('start_date', '9999'), reverse=True)
        
        return sorted_work
    
    def _parse_work_context(self, context: str, date_match: str) -> Optional[Dict]:
        """Parse work entry from context around date"""
        # Look for company and position in context
        lines = context.split('\n')
        
        company = None
        position = None
        
        for line in lines:
            # Check if line contains job title
            for title in self.work_patterns['job_titles_dutch'] + self.work_patterns['job_titles_english']:
                if title.lower() in line.lower():
                    position = line.strip()
                    break
            
            # Check if line contains company indicator
            for indicator in self.work_patterns['company_indicators']:
                if indicator in line:
                    company = line.strip()
                    break
        
        if company or position:
            return {
                'company': company or 'Unknown Company',
                'position': position or 'Unknown Position',
                'start_date': date_match,
                'end_date': None,
                'is_current': any(kw in context.lower() for kw in ['heden', 'present', 'nu']),
                'projects': [],
                'description': context[:200]
            }
        
        return None
    
    def _extract_education(self, sections: Dict, text: str) -> List[Dict]:
        """Extract education using pattern matching"""
        education = []
        
        # Look for education keywords
        edu_keywords = ['bachelor', 'master', 'hbo', 'mbo', 'universiteit', 'hogeschool', 'university', 'college']
        
        lines = text.split('\n')
        for line in lines:
            if any(kw in line.lower() for kw in edu_keywords):
                edu_entry = {
                    'degree': line.strip()[:100],
                    'institution': 'Unknown Institution',
                    'period': None,
                    'graduation_year': None
                }
                education.append(edu_entry)
        
        return education[:5]
    
    def _extract_skills(self, sections: Dict, text: str) -> List[str]:
        """Extract skills from text"""
        skills = []
        
        # Common skill keywords
        skill_keywords = [
            'project management', 'planning', 'primavera', 'microsoft project',
            'autocad', 'excel', 'word', 'powerpoint', 'office',
            'bim', 'revit', 'engineering', 'management'
        ]
        
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                skills.append(skill.title())
        
        return skills[:15]
    
    def _extract_languages(self, sections: Dict, text: str) -> List[str]:
        """Extract language skills"""
        return []
    
    def _extract_courses(self, sections: Dict, text: str) -> List[Dict]:
        """Extract courses/certifications"""
        return []
    
    def _extract_profile(self, sections: Dict, text: str) -> Optional[str]:
        """Extract profile/summary"""
        # Look for profile section
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ['profiel', 'profile', 'samenvatting', 'summary']):
                # Get next 5 lines as profile
                profile_lines = lines[i+1:i+6]
                profile_text = ' '.join([l.strip() for l in profile_lines if l.strip()])
                if len(profile_text) > 50:
                    return profile_text[:500]
        
        return None
    
    def _extract_name_from_filename(self, filename: str) -> Optional[str]:
        """Extract name from filename"""
        # Remove extension
        name = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '')
        
        # Remove CV prefix
        for prefix in ['CV', 'cv', 'Resume', 'resume', 'Resumé']:
            name = name.replace(prefix, '').strip()
        
        # Remove years
        name = re.sub(r'\d{4}', '', name).strip()
        
        # Clean up
        name = name.replace('_', ' ').replace('-', ' ').strip()
        
        if len(name) > 3 and len(name) < 50:
            return name
        
        return None
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if string looks like a name"""
        if not name or len(name) < 3:
            return False
        
        # Check against invalid names
        invalid_names = self.name_patterns.get('invalid_names', [])
        if name in invalid_names:
            return False
        
        # Should not contain numbers
        if re.search(r'\d', name):
            return False
        
        return True
    
    def _extract_birth_year(self, text: str) -> Optional[int]:
        """Extract birth year from text"""
        patterns = [
            r'(?:geboren|born|geboortedatum|birth\s*date).*?(19\d{2}|20[01]\d)',
            r'\b(19[4-9]\d|20[01]\d)\b.*?(?:geboren|born)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    year = int(match.group(1))
                    if 1940 <= year <= 2010:
                        return year
                except:
                    continue
        
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location/city"""
        # Dutch cities
        cities = [
            'Amsterdam', 'Rotterdam', 'Den Haag', 'Utrecht', 'Eindhoven',
            'Groningen', 'Tilburg', 'Almere', 'Breda', 'Nijmegen',
            'Amersfoort', 'Apeldoorn', 'Arnhem', 'Haarlem', 'Enschede'
        ]
        
        text_lower = text.lower()
        for city in cities:
            if city.lower() in text_lower:
                return city
        
        return None
    
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

__all__ = ['PatternStrategy']

