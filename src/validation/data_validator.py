#!/usr/bin/env python3
"""
Data Validator - Generic validation rules for extracted CV data
Validates that extracted data is sensible and not extraction errors
"""

import json
import re
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from src.core.logger import setup_logger

class DataValidator:
    """
    Generic validator for CV data
    Uses pattern libraries to validate extracted data
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Load pattern libraries for validation
        self._load_patterns()
    
    def _load_patterns(self):
        """Load pattern libraries for validation"""
        patterns_dir = Path("src/extraction/patterns")
        
        # Load name patterns
        with open(patterns_dir / "name_patterns.json", 'r', encoding='utf-8') as f:
            name_patterns = json.load(f)
            self.invalid_names = set(name_patterns.get('invalid_names', []))
        
        # Load work patterns
        with open(patterns_dir / "work_patterns.json", 'r', encoding='utf-8') as f:
            work_patterns = json.load(f)
            self.section_headers = set(work_patterns.get('section_not_company', []))
        
        self.logger.info(f"Loaded validation patterns: {len(self.invalid_names)} invalid names, {len(self.section_headers)} section headers")
    
    def validate_all(self, extracted_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate all fields in extracted data
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Validate personal info
        personal_info = extracted_data.get('personal_info', {})
        if personal_info:
            name_valid, name_issue = self.validate_name(personal_info.get('full_name'))
            if not name_valid:
                issues.append(f"Name: {name_issue}")
            
            birth_valid, birth_issue = self.validate_birth_year(personal_info.get('birth_year'))
            if not birth_valid:
                issues.append(f"Birth year: {birth_issue}")
        
        # Validate work experience
        work_exp = extracted_data.get('work_experience', [])
        for i, work in enumerate(work_exp):
            company_valid, company_issue = self.validate_company(work.get('company'))
            if not company_valid:
                issues.append(f"Work {i+1} company: {company_issue}")
            
            date_valid, date_issue = self.validate_date_range(
                work.get('start_date'), 
                work.get('end_date')
            )
            if not date_valid:
                issues.append(f"Work {i+1} dates: {date_issue}")
            
            # Validate one project per entry
            project_valid, project_issue = self.validate_one_project_per_entry(work, i)
            if not project_valid:
                issues.append(project_issue)
        
        # Determine if data is valid
        is_valid = len(issues) == 0 or (len(issues) <= 2 and len(work_exp) > 0)
        
        return is_valid, issues
    
    def validate_name(self, name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that name is an actual name, not a field label
        
        Returns:
            (is_valid, error_message)
        """
        if not name:
            return False, "Name is missing"
        
        # Check if it's an invalid name (field label)
        if name in self.invalid_names:
            return False, f"Field label extracted instead of actual name: '{name}'"
        
        # Check name length
        if len(name) < 3:
            return False, f"Name too short: '{name}'"
        
        if len(name) > 50:
            return False, f"Name too long: '{name}'"
        
        # Check if it contains numbers (usually invalid)
        if re.search(r'\d', name):
            return False, f"Name contains numbers: '{name}'"
        
        # Check word count (1-4 words typical for names)
        words = name.split()
        if len(words) < 1 or len(words) > 4:
            return False, f"Name has unusual word count ({len(words)}): '{name}'"
        
        return True, None
    
    def validate_birth_year(self, birth_year: Optional[int]) -> Tuple[bool, Optional[str]]:
        """
        Validate birth year is reasonable
        
        Returns:
            (is_valid, error_message)
        """
        if birth_year is None:
            return True, None  # Optional field, None is OK
        
        # Check if it's a reasonable year
        if not isinstance(birth_year, int):
            try:
                birth_year = int(birth_year)
            except:
                return False, f"Birth year is not a number: {birth_year}"
        
        # Should be between 1940 and 2010 for professional CVs
        if birth_year < 1940 or birth_year > 2010:
            return False, f"Birth year out of reasonable range: {birth_year}"
        
        return True, None
    
    def validate_company(self, company: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that company is not a section header
        
        Returns:
            (is_valid, error_message)
        """
        if not company:
            return True, None  # Optional, None is OK
        
        # Check if it's a section header (not a company)
        if company in self.section_headers:
            return False, f"Section header extracted as company: '{company}'"
        
        # Check length
        if len(company) < 2:
            return False, f"Company name too short: '{company}'"
        
        return True, None
    
    def validate_date_range(self, start_date: Optional[str], end_date: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that date range makes sense
        
        Returns:
            (is_valid, error_message)
        """
        if not start_date:
            return True, None  # Optional
        
        # Extract years from dates
        start_year = self._extract_year(start_date)
        end_year = self._extract_year(end_date) if end_date else None
        
        if start_year:
            # Check reasonable range
            if start_year < 1960 or start_year > 2025:
                return False, f"Start year out of range: {start_year}"
            
            # Check if end > start
            if end_year and end_year < start_year:
                return False, f"End year ({end_year}) before start year ({start_year})"
        
        return True, None
    
    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string"""
        if not date_str:
            return None
        
        # Try to extract 4-digit year
        match = re.search(r'(19\d{2}|20[0-2]\d)', str(date_str))
        if match:
            return int(match.group(1))
        
        return None
    
    def validate_one_project_per_entry(self, work_entry: Dict, index: int) -> Tuple[bool, Optional[str]]:
        """
        Validate that work_experience entry has at most 1 project
        
        Returns:
            (is_valid, error_message)
        """
        projects = work_entry.get('projects', [])
        
        # No projects or 1 project is valid
        if len(projects) <= 1:
            return True, None
        
        # Multiple projects is a violation (should have been split)
        company = work_entry.get('company', 'Unknown')
        return False, f"Work entry {index+1} ({company}) has {len(projects)} projects (should be 1 per entry)"

__all__ = ['DataValidator']

