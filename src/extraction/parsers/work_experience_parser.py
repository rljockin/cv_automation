#!/usr/bin/env python3
"""
Work Experience Parser - Parse work history from CV sections
MOST COMPLEX PARSER - extracts companies, positions, dates, projects, responsibilities
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date

from src.core import Language, clean_text
from .date_parser import DateParser, ParsedDate


@dataclass
class WorkExperience:
    """Work experience entry"""
    company: Optional[str]
    position: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    is_current: bool
    location: Optional[str]
    description: Optional[str]
    responsibilities: List[str]
    projects: List[str]
    technologies: List[str]
    duration_months: Optional[int]
    confidence: float
    original_text: str


class WorkExperienceParser:
    """
    Parse work experience from CV sections
    
    MOST COMPLEX PARSER - handles:
    - Multiple job formats and styles
    - Various date formats
    - Company name extraction
    - Position title extraction
    - Responsibility parsing
    - Project identification
    - Technology extraction
    - Duration calculation
    
    Strategy:
    1. Split work experience section into individual jobs
    2. Parse each job entry separately
    3. Extract structured data for each job
    4. Validate and clean extracted data
    """
    
    def __init__(self):
        """Initialize work experience parser"""
        
        self.date_parser = DateParser()
        
        # Common job separators
        self.job_separators = [
            r'\n\s*\n',  # Double newline
            r'\n\s*[-=*]\s*\n',  # Line with dashes/equals/stars
            r'\n\s*\d+\.\s*\n',  # Numbered items
            r'\n\s*[A-Z][a-z]+\s+\d{4}',  # Month Year pattern
        ]
        
        # Company indicators
        self.company_indicators = [
            r'(?:bij|at|@|werkzaam\s*bij|employed\s*at)\s+([A-Za-z0-9\s&.,-]+)',
            r'([A-Za-z0-9\s&.,-]+)\s+(?:bv|nv|bv\.|nv\.|ltd|inc|corp|company)',
            r'([A-Za-z0-9\s&.,-]+)\s+(?:consultancy|consulting|engineering|technologies)',
        ]
        
        # Position indicators
        self.position_indicators = [
            r'(?:functie|position|role|title)\s*:?\s*([A-Za-z0-9\s&.,-]+)',
            r'(?:als|as)\s+([A-Za-z0-9\s&.,-]+)',
            r'([A-Za-z0-9\s&.,-]+)\s+(?:projectmanager|consultant|engineer|specialist)',
        ]
        
        # Responsibility indicators
        self.responsibility_indicators = [
            r'(?:verantwoordelijkheden|responsibilities|tasks|taken)\s*:?\s*',
            r'(?:werkzaamheden|activities|duties)\s*:?\s*',
            r'(?:resultaten|results|achievements)\s*:?\s*',
        ]
        
        # Project indicators
        self.project_indicators = [
            r'(?:projecten|projects)\s*:?\s*',
            r'(?:project|project\s*name)\s*:?\s*',
            r'(?:klant|client|customer)\s*:?\s*',
        ]
        
        # Technology indicators
        self.technology_indicators = [
            r'(?:technologieën|technologies|tools|software)\s*:?\s*',
            r'(?:programmeertalen|programming\s*languages)\s*:?\s*',
            r'(?:methoden|methods|methodologies)\s*:?\s*',
        ]
    
    def parse_work_experience(self, work_section: str, language: Language = Language.UNKNOWN) -> List[WorkExperience]:
        """
        Parse work experience section
        
        Args:
            work_section: Text from work experience section
            language: Detected language
            
        Returns:
            List of WorkExperience objects
        """
        if not work_section or len(work_section.strip()) < 50:
            return []
        
        # Clean text
        work_section = clean_text(work_section)
        
        # Split into individual job entries
        job_entries = self._split_into_jobs(work_section)
        
        # Parse each job entry
        work_experiences = []
        for job_text in job_entries:
            if len(job_text.strip()) < 20:
                continue
            
            work_exp = self._parse_single_job(job_text, language)
            if work_exp:
                work_experiences.append(work_exp)
        
        # Sort by start date (most recent first)
        work_experiences.sort(key=lambda x: x.start_date or date.min, reverse=True)
        
        return work_experiences
    
    def _split_into_jobs(self, text: str) -> List[str]:
        """Split work experience text into individual job entries"""
        
        # Try different splitting strategies
        jobs = []
        
        # Strategy 1: Split on date patterns
        date_split_jobs = self._split_on_dates(text)
        if len(date_split_jobs) > 1:
            jobs.extend(date_split_jobs)
        
        # Strategy 2: Split on company patterns
        company_split_jobs = self._split_on_companies(text)
        if len(company_split_jobs) > 1:
            jobs.extend(company_split_jobs)
        
        # Strategy 3: Split on common separators
        separator_split_jobs = self._split_on_separators(text)
        if len(separator_split_jobs) > 1:
            jobs.extend(separator_split_jobs)
        
        # If no splitting worked, treat entire text as one job
        if not jobs:
            jobs = [text]
        
        # Clean and filter jobs
        cleaned_jobs = []
        for job in jobs:
            job = job.strip()
            if len(job) >= 20:  # Minimum length
                cleaned_jobs.append(job)
        
        return cleaned_jobs
    
    def _split_on_dates(self, text: str) -> List[str]:
        """Split text on date patterns"""
        
        # Find all dates in text
        dates = self.date_parser.parse_all_dates(text)
        
        if len(dates) < 2:
            return []
        
        # Split text at date positions
        jobs = []
        lines = text.split('\n')
        
        current_job = []
        for line in lines:
            line = line.strip()
            if not line:
                if current_job:
                    current_job.append('')
                continue
            
            # Check if line contains a date
            line_dates = self.date_parser.parse_all_dates(line)
            if line_dates and current_job:
                # Start new job
                jobs.append('\n'.join(current_job))
                current_job = [line]
            else:
                current_job.append(line)
        
        # Add last job
        if current_job:
            jobs.append('\n'.join(current_job))
        
        return jobs
    
    def _split_on_companies(self, text: str) -> List[str]:
        """Split text on company name patterns"""
        
        jobs = []
        lines = text.split('\n')
        
        current_job = []
        for line in lines:
            line = line.strip()
            if not line:
                if current_job:
                    current_job.append('')
                continue
            
            # Check if line looks like a company name
            if self._is_company_line(line) and current_job:
                # Start new job
                jobs.append('\n'.join(current_job))
                current_job = [line]
            else:
                current_job.append(line)
        
        # Add last job
        if current_job:
            jobs.append('\n'.join(current_job))
        
        return jobs
    
    def _split_on_separators(self, text: str) -> List[str]:
        """Split text on common separators"""
        
        jobs = []
        current_job = []
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for separator patterns
            is_separator = False
            for pattern in self.job_separators:
                if re.search(pattern, line):
                    is_separator = True
                    break
            
            if is_separator and current_job:
                jobs.append('\n'.join(current_job))
                current_job = []
            else:
                current_job.append(line)
        
        # Add last job
        if current_job:
            jobs.append('\n'.join(current_job))
        
        return jobs
    
    def _is_company_line(self, line: str) -> bool:
        """Check if line looks like a company name"""
        
        # Must be reasonable length
        if len(line) < 3 or len(line) > 100:
            return False
        
        # Should not contain common CV words
        cv_words = ['werkervaring', 'experience', 'verantwoordelijkheden', 'responsibilities']
        if any(word in line.lower() for word in cv_words):
            return False
        
        # Should not be all caps (unless short)
        if line.isupper() and len(line) > 15:
            return False
        
        # Check for company indicators
        for pattern in self.company_indicators:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Check for common company suffixes
        company_suffixes = ['bv', 'nv', 'bv.', 'nv.', 'ltd', 'inc', 'corp', 'company', 'consultancy', 'consulting']
        if any(line.lower().endswith(suffix) for suffix in company_suffixes):
            return True
        
        return False
    
    def _parse_single_job(self, job_text: str, language: Language) -> Optional[WorkExperience]:
        """Parse a single job entry"""
        
        # Extract different components
        company = self._extract_company(job_text)
        position = self._extract_position(job_text)
        start_date, end_date, is_current = self._extract_dates(job_text)
        location = self._extract_location(job_text)
        description = self._extract_description(job_text)
        responsibilities = self._extract_responsibilities(job_text)
        projects = self._extract_projects(job_text)
        technologies = self._extract_technologies(job_text)
        
        # Calculate duration
        duration_months = self._calculate_duration(start_date, end_date, is_current)
        
        # Calculate confidence
        confidence = self._calculate_confidence({
            'company': company,
            'position': position,
            'start_date': start_date,
            'description': description
        })
        
        # Only create if we have minimum required data
        if not company and not position:
            return None
        
        return WorkExperience(
            company=company,
            position=position,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            location=location,
            description=description,
            responsibilities=responsibilities,
            projects=projects,
            technologies=technologies,
            duration_months=duration_months,
            confidence=confidence,
            original_text=job_text
        )
    
    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company name"""
        
        # Try company indicators
        for pattern in self.company_indicators:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up company name
                company = re.sub(r'\s+', ' ', company)
                return company
        
        # Try to find company in first few lines
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if self._is_company_line(line):
                return line
        
        return None
    
    def _extract_position(self, text: str) -> Optional[str]:
        """Extract position/title"""
        
        # Try position indicators
        for pattern in self.position_indicators:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                position = match.group(1).strip()
                # Clean up position
                position = re.sub(r'\s+', ' ', position)
                return position
        
        # Look for common position patterns
        position_patterns = [
            r'(projectmanager|project\s*manager)',
            r'(consultant|adviseur)',
            r'(engineer|ingenieur)',
            r'(specialist|expert)',
            r'(manager|leidinggevende)',
            r'(developer|ontwikkelaar)',
            r'(analyst|analist)',
        ]
        
        for pattern in position_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_dates(self, text: str) -> Tuple[Optional[date], Optional[date], bool]:
        """Extract start and end dates"""
        
        dates = self.date_parser.parse_all_dates(text)
        
        if not dates:
            return None, None, False
        
        # Sort dates by start date
        dates.sort(key=lambda d: d.start_date or date.min)
        
        # Take first date as start, last as end
        start_date = dates[0].start_date
        end_date = dates[-1].end_date if len(dates) > 1 else None
        is_current = dates[-1].is_present if dates else False
        
        return start_date, end_date, is_current
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract job location"""
        
        # Look for location patterns
        location_patterns = [
            r'(?:locatie|location|plaats|place)\s*:?\s*([A-Za-z\s,.-]+)',
            r'(?:in|at|@)\s+([A-Za-z\s,.-]+?)(?:\n|$|,|\s{2,})',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up location
                location = re.sub(r'\s+', ' ', location)
                return location
        
        return None
    
    def _extract_description(self, text: str) -> Optional[str]:
        """Extract job description"""
        
        # Look for description patterns
        description_patterns = [
            r'(?:beschrijving|description|overview)\s*:?\s*(.+?)(?:\n\s*\n|$)',
            r'(?:samenvatting|summary)\s*:?\s*(.+?)(?:\n\s*\n|$)',
        ]
        
        for pattern in description_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                description = match.group(1).strip()
                if len(description) > 20:
                    return description
        
        return None
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract responsibilities/tasks"""
        
        responsibilities = []
        
        # Look for responsibility sections
        for pattern in self.responsibility_indicators:
            match = re.search(pattern + r'(.+?)(?:\n\s*\n|$)', text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Split into individual responsibilities
                items = re.split(r'\n\s*[-•*]\s*', content)
                for item in items:
                    item = item.strip()
                    if len(item) > 10:
                        responsibilities.append(item)
        
        return responsibilities
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract projects"""
        
        projects = []
        
        # Look for project sections
        for pattern in self.project_indicators:
            match = re.search(pattern + r'(.+?)(?:\n\s*\n|$)', text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Split into individual projects
                items = re.split(r'\n\s*[-•*]\s*', content)
                for item in items:
                    item = item.strip()
                    if len(item) > 10:
                        projects.append(item)
        
        return projects
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technologies/tools"""
        
        technologies = []
        
        # Look for technology sections
        for pattern in self.technology_indicators:
            match = re.search(pattern + r'(.+?)(?:\n\s*\n|$)', text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Split into individual technologies
                items = re.split(r'[,;]\s*', content)
                for item in items:
                    item = item.strip()
                    if len(item) > 2:
                        technologies.append(item)
        
        return technologies
    
    def _calculate_duration(self, start_date: Optional[date], end_date: Optional[date], is_current: bool) -> Optional[int]:
        """Calculate job duration in months"""
        
        if not start_date:
            return None
        
        if is_current:
            end_date = date.today()
        elif not end_date:
            return None
        
        # Calculate months
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        return max(0, months)
    
    def _calculate_confidence(self, extracted_data: Dict) -> float:
        """Calculate confidence score"""
        
        confidence = 0.0
        
        # Company
        if extracted_data.get('company'):
            confidence += 0.3
        
        # Position
        if extracted_data.get('position'):
            confidence += 0.3
        
        # Start date
        if extracted_data.get('start_date'):
            confidence += 0.2
        
        # Description
        if extracted_data.get('description'):
            confidence += 0.2
        
        return confidence
