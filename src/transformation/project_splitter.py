#!/usr/bin/env python3
"""
Project Splitter
Generic utility to split grouped projects into individual work_experience entries
"""

import re
from typing import List, Dict, Optional
from src.core.logger import setup_logger

logger = setup_logger(__name__)


class ProjectSplitter:
    """
    Generic utility to split work entries with multiple projects
    
    Ensures each work_experience entry has exactly ONE project
    Applies to both ZZP and loondienst CVs
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        logger.info("ProjectSplitter initialized")
    
    def split_grouped_projects(self, work_experience: List[Dict]) -> List[Dict]:
        """
        Split work entries that have multiple projects into individual entries
        
        Args:
            work_experience: Original work_experience array (may have grouping)
        
        Returns:
            Expanded work_experience array (one project per entry)
        """
        if not work_experience:
            return []
        
        expanded = []
        split_count = 0
        
        for work_entry in work_experience:
            projects = work_entry.get('projects', [])
            
            # Case 1: No projects or empty projects → Keep as is
            if not projects or len(projects) == 0:
                expanded.append(work_entry)
                continue
            
            # Case 2: Only 1 project → Keep as is (already correct)
            if len(projects) == 1:
                expanded.append(work_entry)
                continue
            
            # Case 3: Multiple projects → SPLIT into separate entries
            self.logger.info(f"Splitting {len(projects)} projects from {work_entry.get('company', 'Unknown')} into separate entries")
            split_count += len(projects)
            
            for project in projects:
                # Create new work_experience entry for THIS project only
                new_entry = {
                    'company': self._get_company_for_project(work_entry, project),
                    'position': self._get_position_for_project(work_entry, project),
                    'start_date': self._extract_start_date(project, work_entry),
                    'end_date': self._extract_end_date(project, work_entry),
                    'is_current': self._is_current(project, work_entry),
                    'location': work_entry.get('location'),
                    'projects': [project]  # ONLY this one project
                }
                
                expanded.append(new_entry)
        
        self.logger.info(f"Splitting complete: {len(work_experience)} entries → {len(expanded)} entries ({split_count} projects split)")
        
        return expanded
    
    def _get_company_for_project(self, work_entry: Dict, project: Dict) -> str:
        """
        Get company name for this specific project
        
        If project has client, combine: "Company (voor Client)"
        Otherwise use work_entry company
        """
        company = work_entry.get('company', 'Unknown')
        client = project.get('client')
        
        # If project has a client, add it to company name
        if client and client.lower() not in company.lower():
            return f"{company} (voor {client})"
        
        return company
    
    def _get_position_for_project(self, work_entry: Dict, project: Dict) -> str:
        """
        Get position/role for this specific project
        
        Priority:
        1. project.role (most specific)
        2. work_entry.position (fallback)
        """
        # Try project-specific role first
        role = project.get('role')
        if role:
            return role
        
        # Fallback to work_entry position
        position = work_entry.get('position')
        if position:
            return position
        
        return 'Unknown'
    
    def _extract_start_date(self, project: Dict, work_entry: Dict) -> Optional[str]:
        """
        Extract start date from project or work entry
        
        Priority:
        1. project.period (extract start)
        2. work_entry.start_date (fallback)
        """
        # Try project period first
        period = project.get('period')
        if period:
            # Extract start year from period string
            # Formats: "2020-2021", "2020 - 2021", "Jan 2020 - Dec 2021", "2020-heden"
            match = re.search(r'(19\d{2}|20[0-2]\d)', str(period))
            if match:
                return match.group(1)
        
        # Fallback to work_entry start_date
        return work_entry.get('start_date')
    
    def _extract_end_date(self, project: Dict, work_entry: Dict) -> Optional[str]:
        """
        Extract end date from project or work entry
        
        Priority:
        1. project.period (extract end)
        2. work_entry.end_date (fallback)
        """
        # Try project period first
        period = project.get('period')
        if period:
            period_str = str(period).lower()
            
            # Check if current/ongoing
            if any(kw in period_str for kw in ['heden', 'present', 'nu', 'current']):
                return None  # Current project
            
            # Extract end year from period
            # Find all 4-digit years
            years = re.findall(r'(19\d{2}|20[0-2]\d)', str(period))
            if len(years) >= 2:
                return years[-1]  # Last year is end date
            elif len(years) == 1:
                return years[0]  # Single year (start = end)
        
        # Fallback to work_entry end_date
        return work_entry.get('end_date')
    
    def _is_current(self, project: Dict, work_entry: Dict) -> bool:
        """
        Determine if project is current/ongoing
        """
        # Check project period
        period = project.get('period', '')
        if any(kw in str(period).lower() for kw in ['heden', 'present', 'nu', 'current']):
            return True
        
        # Check if no end_date was extracted
        end_date = self._extract_end_date(project, work_entry)
        if not end_date:
            # Check if work_entry is current
            return work_entry.get('is_current', False)
        
        return False


__all__ = ['ProjectSplitter']

