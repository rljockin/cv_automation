#!/usr/bin/env python3
"""
Work Experience Section Merger
Generic utility to merge work experience from multiple CV sections
"""

import re
from typing import Dict, List, Tuple, Optional
from src.core.logger import setup_logger

logger = setup_logger(__name__)


class WorkExperienceMerger:
    """
    Generic utility to merge work experience from multiple sections
    Handles patterns like:
    - Ervaring + Projecten
    - Loopbaan + Relevante werkervaring
    - Work Experience + Projects
    - Any combination of work-related sections
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        logger.info("WorkExperienceMerger initialized")
    
    def merge_work_sections(self, sections_data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Merge work experience from multiple section sources
        
        Args:
            sections_data: Dictionary mapping section names to work entries
                {
                    'Work Experience': [{work1}, {work2}],
                    'Projects': [{proj1}, {proj2}, ...],
                    'Career': [{career1}]
                }
        
        Returns:
            Combined list of unique work experience entries, sorted by date
        """
        all_entries = []
        
        # Combine all entries from all sections
        for section_name, entries in sections_data.items():
            if entries:
                logger.debug(f"Merging {len(entries)} entries from section: {section_name}")
                all_entries.extend(entries)
        
        logger.info(f"Total entries before deduplication: {len(all_entries)}")
        
        # Remove duplicates
        unique_entries = self._remove_duplicates(all_entries)
        
        logger.info(f"Total entries after deduplication: {len(unique_entries)}")
        
        # Sort by date (most recent first)
        sorted_entries = self._sort_by_date(unique_entries)
        
        return sorted_entries
    
    def _remove_duplicates(self, entries: List[Dict]) -> List[Dict]:
        """
        Remove duplicate work entries
        
        Duplicates are identified by matching:
        - Company name (normalized)
        - Position (normalized)
        - Start date
        
        This is generic - works for any work entry structure
        """
        seen = set()
        unique = []
        
        for entry in entries:
            # Create unique key from core fields
            company = self._normalize_text(entry.get('company', ''))
            position = self._normalize_text(entry.get('position', ''))
            start_date = entry.get('start_date', '').strip()
            
            # Create key
            key = f"{company}|{position}|{start_date}"
            
            # Only add if not seen and has meaningful data
            if key not in seen and (company or position):
                seen.add(key)
                unique.append(entry)
            else:
                if key in seen:
                    logger.debug(f"Duplicate removed: {company} - {position} ({start_date})")
        
        return unique
    
    def _sort_by_date(self, entries: List[Dict]) -> List[Dict]:
        """
        Sort work entries by start date (most recent first)
        
        Handles:
        - YYYY format
        - Missing dates (puts at end)
        - "heden"/"present" in end_date
        """
        def get_sort_key(entry: Dict) -> str:
            start_date = entry.get('start_date', '')
            
            # Extract year from date string
            if start_date:
                # Try to extract 4-digit year
                match = re.search(r'(19\d{2}|20[0-2]\d)', str(start_date))
                if match:
                    return match.group(1)
            
            # If no date found, return very old date to sort to end
            return '0000'
        
        # Sort descending (most recent first)
        sorted_entries = sorted(entries, key=get_sort_key, reverse=True)
        
        return sorted_entries
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison
        - Lowercase
        - Remove extra whitespace
        - Remove special characters
        """
        if not text:
            return ''
        
        # Lowercase
        normalized = text.lower()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove common variations
        normalized = normalized.replace('bv', '').replace('b.v.', '').replace('nv', '')
        normalized = normalized.strip('. ')
        
        return normalized
    
    def merge_with_employers(
        self, 
        employers: List[Dict], 
        projects: List[Dict]
    ) -> List[Dict]:
        """
        Special case: Merge employer timeline with detailed project list
        
        Pattern: "Loopbaan" section has employers, "Projecten" has detailed projects
        
        Args:
            employers: List of employer entries (usually from "Loopbaan" section)
            projects: List of project entries (usually from "Projecten" section)
        
        Returns:
            Combined work experience with projects matched to employers by date
        """
        result = []
        
        # If no employers, just return projects
        if not employers:
            return projects
        
        # If no projects, just return employers
        if not projects:
            return employers
        
        # Match projects to employers by date overlap
        for project in projects:
            project_start = self._extract_year(project.get('start_date'))
            project_end = self._extract_year(project.get('end_date'))
            
            matched = False
            
            # Try to find matching employer by date overlap
            for employer in employers:
                emp_start = self._extract_year(employer.get('start_date'))
                emp_end = self._extract_year(employer.get('end_date'))
                
                if self._dates_overlap(project_start, project_end, emp_start, emp_end):
                    # Date overlap found - this project belongs to this employer
                    # Add project entry with employer context
                    combined_entry = project.copy()
                    if not combined_entry.get('company') and employer.get('company'):
                        combined_entry['company'] = employer['company']
                    matched = True
                    result.append(combined_entry)
                    break
            
            # If no employer match, add project standalone
            if not matched:
                result.append(project)
        
        # Add employers without matching projects
        for employer in employers:
            has_match = False
            emp_start = self._extract_year(employer.get('start_date'))
            emp_end = self._extract_year(employer.get('end_date'))
            
            for project in projects:
                proj_start = self._extract_year(project.get('start_date'))
                proj_end = self._extract_year(project.get('end_date'))
                
                if self._dates_overlap(proj_start, proj_end, emp_start, emp_end):
                    has_match = True
                    break
            
            # Add employer if no projects matched to it
            if not has_match:
                result.append(employer)
        
        return result
    
    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string"""
        if not date_str:
            return None
        
        match = re.search(r'(19\d{2}|20[0-2]\d)', str(date_str))
        if match:
            return int(match.group(1))
        
        return None
    
    def _dates_overlap(
        self, 
        start1: Optional[int], 
        end1: Optional[int], 
        start2: Optional[int], 
        end2: Optional[int]
    ) -> bool:
        """Check if two date ranges overlap"""
        if not start1 or not start2:
            return False
        
        # If no end dates, assume current
        if not end1:
            end1 = 2025
        if not end2:
            end2 = 2025
        
        # Check overlap
        return not (end1 < start2 or end2 < start1)


__all__ = ['WorkExperienceMerger']

