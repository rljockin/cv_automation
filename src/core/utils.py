#!/usr/bin/env python3
"""
Core Utilities - Helper functions for CV Automation System
Common utilities used across all components
"""

import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Any
import unicodedata

from .constants import FilePatterns, LanguageIndicators
from .exceptions import FileNotFoundException


# ============================================================================
# FILE UTILITIES
# ============================================================================

def generate_file_id(file_path: str) -> str:
    """Generate unique ID for a file based on path and content"""
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
    return f"{path_hash}_{file_hash[:16]}"


def get_file_extension(file_path: str) -> str:
    """Get file extension in lowercase"""
    return os.path.splitext(file_path)[1].lower()


def is_cv_file(filename: str) -> bool:
    """Check if filename matches CV pattern"""
    for pattern in FilePatterns.CV_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False


def is_resume_file(filename: str) -> bool:
    """Check if filename matches Resumé pattern"""
    for pattern in FilePatterns.RESUME_PATTERNS:
        if re.search(pattern, filename):
            return True
    return False


def get_person_name_from_path(file_path: str, network_folder: str) -> str:
    """Extract person's name from file path (folder name)"""
    try:
        rel_path = os.path.relpath(os.path.dirname(file_path), network_folder)
        # Get first directory name (person's folder)
        person_folder = rel_path.split(os.sep)[0]
        return person_folder if person_folder != '.' else "Unknown"
    except:
        return "Unknown"


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure directory exists, create if not"""
    os.makedirs(directory_path, exist_ok=True)


# ============================================================================
# TEXT UTILITIES
# ============================================================================

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove multiple newlines (keep max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    return ' '.join(text.split())


def extract_name_components(full_name: str) -> Tuple[str, str]:
    """Extract first and last name from full name"""
    if not full_name:
        return "", ""
    
    parts = full_name.strip().split()
    
    if len(parts) == 1:
        return parts[0], parts[0]
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        # Handle middle names, prefixes, etc.
        # For Dutch names like "Jan van der Berg" - last name is everything after first
        first_name = parts[0]
        last_name = ' '.join(parts[1:])
        return first_name, last_name


def extract_city_from_location(location: str) -> str:
    """Extract city name from full address"""
    if not location:
        return ""
    
    # Try to extract just the city (remove postal code, street, etc.)
    lines = location.split('\n')
    for line in lines:
        # Skip lines with only numbers (postal codes)
        if re.match(r'^\d+', line.strip()):
            continue
        # Skip lines with street numbers
        if re.search(r'\d+[a-z]?\s*$', line.strip()):
            continue
        # Return first line that looks like a city name
        clean_line = line.strip()
        if len(clean_line) > 2 and not clean_line.isdigit():
            return clean_line
    
    # Fallback: return first non-empty line
    return location.split('\n')[0].strip()


# ============================================================================
# DATE UTILITIES
# ============================================================================

def extract_year_from_text(text: str) -> Optional[int]:
    """Extract first valid year from text"""
    years = re.findall(r'\b(19[4-9]\d|20[0-2]\d)\b', text)
    if years:
        return int(years[0])
    return None


def is_current_date_indicator(text: str) -> bool:
    """Check if text indicates current/ongoing"""
    text_lower = text.lower()
    indicators = ['heden', 'present', 'now', 'current', 'actueel']
    return any(indicator in text_lower for indicator in indicators)


def normalize_date_format(date_str: str) -> str:
    """Normalize date string to standard format"""
    # Remove extra whitespace
    date_str = date_str.strip()
    
    # Replace various dash types with standard dash
    date_str = re.sub(r'\s*[–—−]\s*', ' – ', date_str)
    
    # Normalize "heden" variations
    date_str = re.sub(r'(heden|present|Present|Heden)', 'heden', date_str, flags=re.IGNORECASE)
    
    return date_str


# ============================================================================
# LANGUAGE DETECTION
# ============================================================================

def detect_language(text: str) -> str:
    """Detect primary language of text"""
    if not text or len(text) < 50:
        return "Unknown"
    
    text_lower = text.lower()
    
    # Count Dutch keywords
    dutch_count = sum(1 for keyword in LanguageIndicators.DUTCH_KEYWORDS 
                     if keyword in text_lower)
    
    # Count English keywords
    english_count = sum(1 for keyword in LanguageIndicators.ENGLISH_KEYWORDS 
                       if keyword in text_lower)
    
    if dutch_count > english_count * 1.5:  # Clear Dutch majority
        return "Dutch"
    elif english_count > dutch_count * 1.5:  # Clear English majority
        return "English"
    elif dutch_count > 0 and english_count > 0:
        return "Mixed (Dutch/English)"
    else:
        return "Unknown"


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def is_valid_birth_year(year: int) -> bool:
    """Check if birth year is reasonable"""
    return 1940 <= year <= 2010


def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """Basic phone validation (Dutch format)"""
    # Remove spaces, dots, dashes
    clean_phone = re.sub(r'[\s\.\-]', '', phone)
    # Check if it matches Dutch phone pattern
    pattern = r'^(\+31|0031|0)[1-9]\d{8,9}$'
    return bool(re.match(pattern, clean_phone))


# ============================================================================
# STRING UTILITIES
# ============================================================================

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def remove_special_characters(text: str) -> str:
    """Remove problematic special characters"""
    # Keep alphanumeric, spaces, common punctuation
    return re.sub(r'[^\w\s\.\,\-\(\)\:\;\'\"]', '', text)


def capitalize_name(name: str) -> str:
    """Properly capitalize a Dutch name"""
    # Handle prefixes like "van", "de", "van der"
    parts = name.split()
    result = []
    
    prefixes = ['van', 'de', 'der', 'den', 'het', 'ter', 'te', 'ten']
    
    for i, part in enumerate(parts):
        if part.lower() in prefixes and i > 0:
            result.append(part.lower())
        else:
            result.append(part.capitalize())
    
    return ' '.join(result)


# ============================================================================
# FORMATTING UTILITIES
# ============================================================================

def format_bullet_points(items: List[str]) -> str:
    """Format list as bullet points"""
    return '\n'.join(f"• {item}" for item in items)


def remove_bullet_points(text: str) -> str:
    """Remove bullet point characters from text"""
    return re.sub(r'^[\•\-\*]\s*', '', text, flags=re.MULTILINE)


# ============================================================================
# PATH UTILITIES
# ============================================================================

def get_person_folder(person_name: str, network_folder: str) -> str:
    """Get path to person's folder"""
    return os.path.join(network_folder, person_name)


def get_resume_output_path(person_name: str, network_folder: str, first_name: str, last_name: str, extension: str = '.docx') -> str:
    """Generate output path for Resumé file"""
    person_folder = get_person_folder(person_name, network_folder)
    filename = f"Resumé_Synergie projectmanagement_{first_name}_{last_name}{extension}"
    return os.path.join(person_folder, filename)


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def format_log_message(level: str, component: str, message: str) -> str:
    """Format log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"[{timestamp}] [{level}] [{component}] {message}"


def log_processing_step(cv_id: str, step: str, status: str, duration: Optional[float] = None) -> str:
    """Format processing step log"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = f"[{timestamp}] [cv_{cv_id}] [{step}] {status}"
    if duration:
        msg += f" ({duration:.2f}s)"
    return msg


# ============================================================================
# PERFORMANCE UTILITIES
# ============================================================================

def calculate_eta(completed: int, total: int, avg_time: float) -> Optional[str]:
    """Calculate estimated time to completion"""
    if total == 0 or avg_time == 0:
        return None
    
    remaining = total - completed
    eta_seconds = remaining * avg_time
    
    if eta_seconds < 60:
        return f"{eta_seconds:.0f} seconds"
    elif eta_seconds < 3600:
        return f"{eta_seconds/60:.1f} minutes"
    else:
        return f"{eta_seconds/3600:.1f} hours"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


# ============================================================================
# DATA STRUCTURE UTILITIES
# ============================================================================

def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Merge two dictionaries, dict2 takes precedence"""
    result = dict1.copy()
    result.update(dict2)
    return result


def flatten_list(nested_list: List[List]) -> List:
    """Flatten a nested list"""
    return [item for sublist in nested_list for item in sublist]


# ============================================================================
# PROGRESS TRACKING
# ============================================================================

class ProgressTracker:
    """Simple progress tracker"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1) -> None:
        """Update progress"""
        self.current += increment
    
    def percentage(self) -> float:
        """Get progress percentage"""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100
    
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def eta(self) -> Optional[str]:
        """Get estimated time remaining"""
        if self.current == 0:
            return None
        avg_time = self.elapsed_time() / self.current
        remaining = self.total - self.current
        eta_seconds = remaining * avg_time
        return format_duration(eta_seconds)
    
    def __str__(self):
        return f"{self.description}: {self.current}/{self.total} ({self.percentage():.1f}%) - ETA: {self.eta()}"


# ============================================================================
# CONSOLE OUTPUT UTILITIES
# ============================================================================

def print_section_header(title: str, width: int = 80, char: str = '='):
    """Print a formatted section header"""
    print(f"\n{char * width}")
    print(f"{title.center(width)}")
    print(f"{char * width}\n")


def print_subsection_header(title: str, width: int = 80, char: str = '-'):
    """Print a formatted subsection header"""
    print(f"\n{title}")
    print(f"{char * width}")


def print_key_value(key: str, value: Any, indent: int = 2):
    """Print key-value pair with formatting"""
    indent_str = " " * indent
    print(f"{indent_str}{key}: {value}")


def print_table_row(columns: List[str], widths: List[int]):
    """Print a formatted table row"""
    row = "  "
    for col, width in zip(columns, widths):
        row += f"{str(col)[:width]:<{width}}  "
    print(row)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_file_exists(file_path: str) -> bool:
    """Check if file exists"""
    return os.path.exists(file_path) and os.path.isfile(file_path)


def validate_file_readable(file_path: str) -> bool:
    """Check if file is readable"""
    try:
        with open(file_path, 'rb') as f:
            f.read(1)
        return True
    except:
        return False


def validate_directory_writable(directory: str) -> bool:
    """Check if directory is writable"""
    try:
        test_file = os.path.join(directory, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except:
        return False


# ============================================================================
# DEBUGGING UTILITIES
# ============================================================================

def debug_print_dict(data: dict, indent: int = 0):
    """Print dictionary in readable format (for debugging)"""
    indent_str = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{indent_str}{key}:")
            debug_print_dict(value, indent + 1)
        elif isinstance(value, list):
            print(f"{indent_str}{key}: [{len(value)} items]")
        else:
            print(f"{indent_str}{key}: {value}")


def safe_get(dictionary: dict, *keys, default=None):
    """Safely get nested dictionary value"""
    value = dictionary
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default
    return value


# ============================================================================
# PERFORMANCE UTILITIES
# ============================================================================

class Timer:
    """Simple timer context manager"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, *args):
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
    
    def __str__(self):
        if self.duration:
            return f"{self.name}: {format_duration(self.duration)}"
        return f"{self.name}: Running..."

