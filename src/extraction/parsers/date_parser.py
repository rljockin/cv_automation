#!/usr/bin/env python3
"""
Date Parser - Parse various date formats in CVs
Handles 7 different date formats found in CV analysis
"""

import re
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum

from src.core import Language


class DateFormat(str, Enum):
    """Supported date formats"""
    YEAR_ONLY = "YYYY"
    YEAR_RANGE = "YYYY - YYYY"
    MONTH_YEAR = "Month YYYY"
    DAY_MONTH_YEAR = "DD-MM-YYYY"
    YEAR_TO_PRESENT = "YYYY - heden"
    MONTH_YEAR_SLASH = "MM/YYYY"
    ISO_DATE = "YYYY-MM-DD"


@dataclass
class ParsedDate:
    """Parsed date information"""
    start_date: Optional[date]
    end_date: Optional[date]
    format_used: DateFormat
    confidence: float
    original_text: str
    is_present: bool


class DateParser:
    """
    Parse dates in various formats found in CVs
    
    Handles 7 formats from CV analysis:
    1. YYYY (e.g., "2020")
    2. YYYY - YYYY (e.g., "2020 - 2022")
    3. Month YYYY (e.g., "Januari 2020")
    4. DD-MM-YYYY (e.g., "15-03-2020")
    5. YYYY - heden (e.g., "2020 - heden")
    6. MM/YYYY (e.g., "03/2020")
    7. YYYY-MM-DD (e.g., "2020-03-15")
    
    Features:
    - Handles Dutch and English month names
    - Detects "present" indicators (heden, present, current)
    - Validates date ranges
    - Provides confidence scores
    - Handles partial dates
    """
    
    def __init__(self):
        """Initialize date parser with patterns"""
        
        # Dutch month names
        self.dutch_months = {
            'januari': 1, 'februari': 2, 'maart': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'augustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'december': 12
        }
        
        # English month names
        self.english_months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        # Present indicators
        self.present_indicators = {
            'heden', 'present', 'current', 'nu', 'now', 'tot heden',
            'to present', 'to current', 'ongoing', 'lopend'
        }
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for date detection"""
        
        # Pattern 1: YYYY
        self.pattern_year = re.compile(r'\b(19|20)\d{2}\b')
        
        # Pattern 2: YYYY - YYYY
        self.pattern_year_range = re.compile(r'\b(19\d{2}|20\d{2})\s*[-–—]\s*(19\d{2}|20\d{2})\b')
        
        # Pattern 3: Month YYYY (Dutch and English)
        dutch_months_str = '|'.join(self.dutch_months.keys())
        english_months_str = '|'.join(self.english_months.keys())
        self.pattern_month_year = re.compile(
            rf'\b({dutch_months_str}|{english_months_str})\s+(19\d{{2}}|20\d{{2}})\b',
            re.IGNORECASE
        )
        
        # Pattern 4: DD-MM-YYYY
        self.pattern_day_month_year = re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/](19\d{2}|20\d{2})\b')
        
        # Pattern 5: YYYY - heden/present
        present_str = '|'.join(self.present_indicators)
        self.pattern_year_present = re.compile(
            rf'\b(19\d{{2}}|20\d{{2}})\s*[-–—]\s*({present_str})\b',
            re.IGNORECASE
        )
        
        # Pattern 6: MM/YYYY
        self.pattern_month_year_slash = re.compile(r'\b\d{1,2}/\d{4}\b')
        
        # Pattern 7: YYYY-MM-DD (ISO)
        self.pattern_iso_date = re.compile(r'\b(19\d{2}|20\d{2})-\d{1,2}-\d{1,2}\b')
    
    def parse_date(self, text: str) -> Optional[ParsedDate]:
        """
        Parse date from text
        
        Args:
            text: Text containing date
            
        Returns:
            ParsedDate object or None if no date found
        """
        if not text or not text.strip():
            return None
        
        text = text.strip()
        
        # Try each pattern in order of specificity
        parsers = [
            self._parse_year_range,
            self._parse_year_present,
            self._parse_month_year,
            self._parse_day_month_year,
            self._parse_month_year_slash,
            self._parse_iso_date,
            self._parse_year_only
        ]
        
        for parser in parsers:
            result = parser(text)
            if result:
                return result
        
        return None
    
    def parse_all_dates(self, text: str) -> List[ParsedDate]:
        """
        Parse all dates in text
        
        Args:
            text: Text to search for dates
            
        Returns:
            List of ParsedDate objects
        """
        dates = []
        
        # Split text into potential date segments
        segments = self._split_text_segments(text)
        
        for segment in segments:
            parsed_date = self.parse_date(segment)
            if parsed_date:
                dates.append(parsed_date)
        
        # Remove duplicates and sort
        dates = self._deduplicate_dates(dates)
        dates.sort(key=lambda d: d.start_date or date.min)
        
        return dates
    
    def _parse_year_range(self, text: str) -> Optional[ParsedDate]:
        """Parse YYYY - YYYY format"""
        
        match = self.pattern_year_range.search(text)
        if not match:
            return None
        
        try:
            start_year = int(match.group(1))
            end_year = int(match.group(2))
            
            # Validate year range
            if start_year > end_year or start_year < 1950 or end_year > 2030:
                return None
            
            start_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            
            return ParsedDate(
                start_date=start_date,
                end_date=end_date,
                format_used=DateFormat.YEAR_RANGE,
                confidence=0.9,
                original_text=match.group(0),
                is_present=False
            )
        
        except (ValueError, TypeError):
            return None
    
    def _parse_year_present(self, text: str) -> Optional[ParsedDate]:
        """Parse YYYY - heden/present format"""
        
        match = self.pattern_year_present.search(text)
        if not match:
            return None
        
        try:
            year = int(match.group(1))
            
            # Validate year
            if year < 1950 or year > 2030:
                return None
            
            start_date = date(year, 1, 1)
            
            return ParsedDate(
                start_date=start_date,
                end_date=None,
                format_used=DateFormat.YEAR_TO_PRESENT,
                confidence=0.95,
                original_text=match.group(0),
                is_present=True
            )
        
        except (ValueError, TypeError):
            return None
    
    def _parse_month_year(self, text: str) -> Optional[ParsedDate]:
        """Parse Month YYYY format"""
        
        match = self.pattern_month_year.search(text)
        if not match:
            return None
        
        try:
            month_name = match.group(1).lower()
            year = int(match.group(2))
            
            # Find month number
            month_num = self.dutch_months.get(month_name) or self.english_months.get(month_name)
            if not month_num:
                return None
            
            # Validate year
            if year < 1950 or year > 2030:
                return None
            
            start_date = date(year, month_num, 1)
            end_date = date(year, month_num, 28)  # Approximate end of month
            
            return ParsedDate(
                start_date=start_date,
                end_date=end_date,
                format_used=DateFormat.MONTH_YEAR,
                confidence=0.85,
                original_text=match.group(0),
                is_present=False
            )
        
        except (ValueError, TypeError):
            return None
    
    def _parse_day_month_year(self, text: str) -> Optional[ParsedDate]:
        """Parse DD-MM-YYYY format"""
        
        match = self.pattern_day_month_year.search(text)
        if not match:
            return None
        
        try:
            parts = re.split(r'[-/]', match.group(0))
            if len(parts) != 3:
                return None
            
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            
            # Validate date
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1950 <= year <= 2030):
                return None
            
            parsed_date = date(year, month, day)
            
            return ParsedDate(
                start_date=parsed_date,
                end_date=parsed_date,
                format_used=DateFormat.DAY_MONTH_YEAR,
                confidence=0.8,
                original_text=match.group(0),
                is_present=False
            )
        
        except (ValueError, TypeError):
            return None
    
    def _parse_month_year_slash(self, text: str) -> Optional[ParsedDate]:
        """Parse MM/YYYY format"""
        
        match = self.pattern_month_year_slash.search(text)
        if not match:
            return None
        
        try:
            parts = match.group(0).split('/')
            if len(parts) != 2:
                return None
            
            month = int(parts[0])
            year = int(parts[1])
            
            # Validate
            if not (1 <= month <= 12 and 1950 <= year <= 2030):
                return None
            
            start_date = date(year, month, 1)
            end_date = date(year, month, 28)  # Approximate end of month
            
            return ParsedDate(
                start_date=start_date,
                end_date=end_date,
                format_used=DateFormat.MONTH_YEAR_SLASH,
                confidence=0.75,
                original_text=match.group(0),
                is_present=False
            )
        
        except (ValueError, TypeError):
            return None
    
    def _parse_iso_date(self, text: str) -> Optional[ParsedDate]:
        """Parse YYYY-MM-DD format"""
        
        match = self.pattern_iso_date.search(text)
        if not match:
            return None
        
        try:
            parts = match.group(0).split('-')
            if len(parts) != 3:
                return None
            
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            
            # Validate
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1950 <= year <= 2030):
                return None
            
            parsed_date = date(year, month, day)
            
            return ParsedDate(
                start_date=parsed_date,
                end_date=parsed_date,
                format_used=DateFormat.ISO_DATE,
                confidence=0.9,
                original_text=match.group(0),
                is_present=False
            )
        
        except (ValueError, TypeError):
            return None
    
    def _parse_year_only(self, text: str) -> Optional[ParsedDate]:
        """Parse YYYY format (fallback)"""
        
        match = self.pattern_year.search(text)
        if not match:
            return None
        
        try:
            year = int(match.group(0))
            
            # Validate year
            if year < 1950 or year > 2030:
                return None
            
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            
            return ParsedDate(
                start_date=start_date,
                end_date=end_date,
                format_used=DateFormat.YEAR_ONLY,
                confidence=0.6,  # Lower confidence for year-only
                original_text=match.group(0),
                is_present=False
            )
        
        except (ValueError, TypeError):
            return None
    
    def _split_text_segments(self, text: str) -> List[str]:
        """Split text into potential date segments"""
        
        # Split on common separators
        segments = re.split(r'[,\n\r\t]', text)
        
        # Clean and filter segments
        cleaned_segments = []
        for segment in segments:
            segment = segment.strip()
            if segment and len(segment) < 100:  # Reasonable length for date
                cleaned_segments.append(segment)
        
        return cleaned_segments
    
    def _deduplicate_dates(self, dates: List[ParsedDate]) -> List[ParsedDate]:
        """Remove duplicate dates"""
        
        seen = set()
        unique_dates = []
        
        for date_obj in dates:
            # Create a key for comparison
            key = (
                date_obj.start_date,
                date_obj.end_date,
                date_obj.is_present,
                date_obj.original_text
            )
            
            if key not in seen:
                seen.add(key)
                unique_dates.append(date_obj)
        
        return unique_dates
    
    def format_date_for_resume(self, parsed_date: ParsedDate) -> str:
        """
        Format parsed date for Resumé output
        
        Args:
            parsed_date: ParsedDate object
            
        Returns:
            Formatted date string for Resumé
        """
        if not parsed_date.start_date:
            return parsed_date.original_text
        
        # Format based on the original format
        if parsed_date.format_used == DateFormat.YEAR_ONLY:
            return str(parsed_date.start_date.year)
        
        elif parsed_date.format_used == DateFormat.YEAR_RANGE:
            if parsed_date.end_date:
                return f"{parsed_date.start_date.year} - {parsed_date.end_date.year}"
            else:
                return str(parsed_date.start_date.year)
        
        elif parsed_date.format_used == DateFormat.MONTH_YEAR:
            month_names = ['', 'Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                          'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
            month_name = month_names[parsed_date.start_date.month]
            return f"{month_name} {parsed_date.start_date.year}"
        
        elif parsed_date.format_used == DateFormat.YEAR_TO_PRESENT:
            return f"{parsed_date.start_date.year} - heden"
        
        else:
            # Default format
            return f"{parsed_date.start_date.year} - {parsed_date.end_date.year if parsed_date.end_date else 'heden'}"
