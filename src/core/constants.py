#!/usr/bin/env python3
"""
Core Constants - System-wide constants for CV Automation
Defines colors, fonts, sizes, and templates based on analysis of 539 Resumés
"""

from dataclasses import dataclass
from docx.shared import RGBColor, Pt, Inches

# ============================================================================
# SYNERGIE BRAND COLORS (From analysis of 539 Resumés)
# ============================================================================

class SynergieColors:
    """Official Synergie brand colors"""
    
    # Primary brand color (used 930 times across all Resumés)
    ORANGE = RGBColor(208, 126, 31)  # #D07E1F
    ORANGE_HEX = "#D07E1F"
    SYNERGIE_ORANGE = (208, 126, 31)  # RGB tuple
    
    # Alternative color (found in some Resumés - older template?)
    TEAL = RGBColor(0, 146, 159)  # #00929F
    TEAL_HEX = "#00929F"
    
    # Standard colors
    BLACK = RGBColor(0, 0, 0)  # #000000
    GRAY = RGBColor(128, 128, 128)  # #808080
    DARK_GRAY = RGBColor(69, 85, 96)  # #455560
    WHITE = RGBColor(255, 255, 255)  # #FFFFFF
    
    # Text color
    TEXT_COLOR = (0, 0, 0)  # Black RGB tuple
    
    # Default section header color (use Orange as primary)
    SECTION_HEADER = ORANGE
    SECTION_HEADER_HEX = ORANGE_HEX


# ============================================================================
# TYPOGRAPHY (From analysis of 539 Resumés)
# ============================================================================

class SynergieFonts:
    """Font specifications"""
    
    # Primary font (used exclusively in 99% of Resumés)
    PRIMARY = "Calibri"
    FONT_FAMILY = "Calibri"
    
    # Fallback fonts (rarely used - avoid)
    FALLBACK = ["Corbel", "Tahoma", "Arial"]
    
    # Font sizes for different elements
    FONT_SIZES = {
        'name': 24,        # Name (24pt)
        'section': 18,     # Section headers (18pt)
        'subsection': 14,  # Subsection headers (14pt)
        'body': 10         # Body text (10pt)
    }


class FontSizes:
    """Font size specifications (in points)"""
    
    # Name/Header sizes
    NAME = Pt(24)           # or Pt(22) - used 157/103 times
    NAME_LARGE = Pt(24)     # Most common for name
    NAME_MEDIUM = Pt(22)    # Alternative for name
    
    # Section headers
    SECTION_HEADER = Pt(18)  # Used 422 times - "Werkervaring", "Opleiding"
    SUB_HEADER = Pt(16)      # Used 269 times - Company names, etc.
    
    # Body text
    BODY_TEXT = Pt(14)       # Used 871 times - Main content
    LOCATION_YEAR = Pt(14)   # Location and birth year
    
    # Table/Detail text
    TABLE_CONTENT = Pt(10)   # Used 587 times - Dates, details
    TABLE_CONTENT_ALT = Pt(11)  # Alternative for table content
    SMALL_DETAIL = Pt(9)     # Smallest size for fine details


# ============================================================================
# PAGE SETUP (A4 Standard)
# ============================================================================

class PageSetup:
    """Page dimensions and margins"""
    
    # Page size (A4)
    WIDTH = Inches(8.27)
    HEIGHT = Inches(11.69)
    
    # Margins (average from 539 Resumés)
    MARGIN_TOP = Inches(1.69)      # Actual from Ronald Smit example
    MARGIN_BOTTOM = Inches(1.18)   # Actual from Ronald Smit example
    MARGIN_LEFT = Inches(0.75)     # Actual from Ronald Smit example
    MARGIN_RIGHT = Inches(0.75)    # Actual from Ronald Smit example
    
    # Alternative margins (from analysis average)
    MARGIN_TOP_AVG = Inches(1.63)
    MARGIN_BOTTOM_AVG = Inches(1.11)
    MARGIN_LEFT_AVG = Inches(0.93)
    MARGIN_RIGHT_AVG = Inches(0.80)


# ============================================================================
# TABLE SPECIFICATIONS
# ============================================================================

class TableSpecs:
    """Table structure specifications"""
    
    # Standard 2-column table widths (from Ronald Smit example)
    DATE_COLUMN_WIDTH = Inches(0.89)     # Left column: ~13% (dates)
    CONTENT_COLUMN_WIDTH = Inches(5.88)  # Right column: ~87% (content)
    
    # Total table width
    TOTAL_WIDTH = Inches(6.77)  # 0.89 + 5.88
    
    # Alternative calculation (percentage-based)
    DATE_COLUMN_PERCENT = 0.13    # 13%
    CONTENT_COLUMN_PERCENT = 0.87  # 87%
    
    # Single column table (for Profile section)
    SINGLE_COLUMN_WIDTH = Inches(6.76)  # From Ronald Smit example
    
    # Average tables per Resumé
    AVERAGE_TABLES = 7
    TYPICAL_RANGE = (5, 10)


# ============================================================================
# SECTION NAMES (Dutch & English)
# ============================================================================

class SectionNames:
    """Standard section names in Resumés"""
    
    # Dutch (primary)
    PROFIEL_NL = "Profiel"
    WERKERVARING_NL = "Werkervaring"
    OPLEIDING_NL = "Opleiding"
    CURSUSSEN_NL = "Cursussen"
    VAARDIGHEDEN_NL = "Vaardigheden"
    TALEN_NL = "Talen"
    SOFTWARE_NL = "Software"
    CERTIFICATEN_NL = "Certificaten"
    
    # English (for English CVs)
    PROFILE_EN = "Profile"
    WORK_EXPERIENCE_EN = "Work Experience"
    EDUCATION_EN = "Education"
    COURSES_EN = "Courses"
    SKILLS_EN = "Skills"
    LANGUAGES_EN = "Languages"
    SOFTWARE_EN = "Software"
    CERTIFICATIONS_EN = "Certifications"


# ============================================================================
# FILE PATTERNS
# ============================================================================

class FilePatterns:
    """File naming and identification patterns"""
    
    # CV identification patterns
    CV_PATTERNS = [
        r'^CV[_ ]',  # Starts with "CV " or "CV_"
        r'^cv[_ ]',  # Lowercase variant
    ]
    
    # Resumé identification patterns
    RESUME_PATTERNS = [
        r'Resumé_Synergie',
        r'Resume_Synergie',
        r'RESUMÉ_Synergie',
    ]
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.PDF', '.DOCX', '.DOC']
    
    # Resumé naming template
    RESUME_FILENAME_TEMPLATE = "Resumé_Synergie projectmanagement_{first_name}_{last_name}.docx"
    RESUME_PDF_TEMPLATE = "Resumé_Synergie projectmanagement_{first_name}_{last_name}.pdf"


# ============================================================================
# PROCESSING CONFIGURATION
# ============================================================================

@dataclass
class ProcessingConfig:
    """Processing behavior configuration"""
    
    # Text extraction thresholds
    min_text_length: int = 100  # Minimum characters for valid extraction
    ocr_threshold: int = 100    # If text < this, try OCR
    
    # File size limits
    min_file_size: int = 10 * 1024        # 10 KB
    max_file_size: int = 50 * 1024 * 1024  # 50 MB
    large_file_threshold: int = 1 * 1024 * 1024  # 1 MB
    
    # Confidence scoring thresholds
    confidence_excellent: float = 0.9   # Auto-approve
    confidence_good: float = 0.7        # Quick review
    confidence_medium: float = 0.5      # Detailed review
    confidence_low: float = 0.3         # Manual processing
    
    # Processing timeouts
    extraction_timeout: int = 60      # seconds
    generation_timeout: int = 30      # seconds
    ocr_timeout: int = 120           # seconds
    
    # Batch processing
    batch_size: int = 10             # Process N files at a time
    max_workers: int = 4             # Parallel workers
    
    # Legacy static attributes for backward compatibility
    MIN_TEXT_LENGTH = 100
    OCR_THRESHOLD = 100
    MIN_FILE_SIZE = 10 * 1024
    MAX_FILE_SIZE = 50 * 1024 * 1024
    LARGE_FILE_THRESHOLD = 1 * 1024 * 1024
    CONFIDENCE_EXCELLENT = 0.9
    CONFIDENCE_GOOD = 0.7
    CONFIDENCE_MEDIUM = 0.5
    CONFIDENCE_LOW = 0.3
    EXTRACTION_TIMEOUT = 60
    GENERATION_TIMEOUT = 30
    OCR_TIMEOUT = 120
    BATCH_SIZE = 10
    MAX_WORKERS = 4


# ============================================================================
# DATE FORMATS
# ============================================================================

class DateFormats:
    """Date format patterns for parsing"""
    
    # Format patterns (regex)
    YYYY = r'\b\d{4}\b'
    YYYY_RANGE = r'\d{4}\s*[-–]\s*\d{4}'
    YYYY_PRESENT = r'\d{4}\s*[-–]\s*(heden|present|now|Heden|Present|Now)'
    MONTH_YYYY = r'\b(jan|feb|mar|apr|may|mei|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+[\'"]?\d{2,4}\b'
    DD_MM_YYYY = r'\d{2}-\d{2}-\d{4}'
    MM_YYYY = r'\d{2}/\d{4}'
    
    # Dutch month names
    DUTCH_MONTHS = {
        'jan': 1, 'januari': 1,
        'feb': 2, 'februari': 2,
        'mrt': 3, 'maart': 3,
        'apr': 4, 'april': 4,
        'mei': 5,
        'jun': 6, 'juni': 6,
        'jul': 7, 'juli': 7,
        'aug': 8, 'augustus': 8,
        'sep': 9, 'september': 9,
        'okt': 10, 'oktober': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    
    # Current indicators
    PRESENT_INDICATORS = ['heden', 'present', 'now', 'current', 'actueel']


# ============================================================================
# SECTION DETECTION PATTERNS
# ============================================================================

class SectionPatterns:
    """Regex patterns for section detection"""
    
    PERSONAL_INFO = [
        r'personalia', r'personal\s+info', r'persoonlijk', 
        r'gegevens', r'personal\s+details'
    ]
    
    PROFILE = [
        r'\bprofiel\b', r'\bprofile\b', r'samenvatting', 
        r'summary', r'over\s+mij', r'about\s+me'
    ]
    
    WORK_EXPERIENCE = [
        r'werkervaring', r'work\s+experience', r'ervaring',
        r'professional\s+experience', r'loopbaan', r'career'
    ]
    
    EDUCATION = [
        r'opleiding', r'education', r'opleidingen', 
        r'scholing', r'academic'
    ]
    
    COURSES = [
        r'cursussen', r'courses', r'training', 
        r'opleidingen', r'certifications'
    ]
    
    SKILLS = [
        r'vaardigheden', r'\bskills\b', r'competenties', 
        r'competencies', r'expertise'
    ]
    
    PROJECTS = [
        r'projecten', r'projects', r'project\s+ervaring',
        r'uitgevoerde\s+projecten'
    ]
    
    LANGUAGES = [
        r'\btalen\b', r'languages', r'talenkennis',
        r'language\s+skills'
    ]
    
    SOFTWARE = [
        r'software', r'\btools\b', r'applicaties',
        r'programma', r'technology'
    ]
    
    CERTIFICATIONS = [
        r'certificaten', r'certificates', r'certificering',
        r'certifications', r'credentials'
    ]


# ============================================================================
# LANGUAGE DETECTION
# ============================================================================

class LanguageIndicators:
    """Language detection keywords"""
    
    DUTCH_KEYWORDS = [
        'werkervaring', 'opleiding', 'vaardigheden', 'persoonlijk',
        'projecten', 'ervaring', 'geboren', 'woonplaats', 'competenties',
        'opleidingen', 'cursussen', 'talen', 'verantwoordelijk',
        'gewerkt', 'beheerd', 'ontwikkeld'
    ]
    
    ENGLISH_KEYWORDS = [
        'work experience', 'education', 'skills', 'personal',
        'projects', 'experience', 'born', 'residence', 'competencies',
        'training', 'languages', 'responsible', 'managed', 
        'developed', 'coordinated'
    ]


# ============================================================================
# STATUS ENUMS (Defined in models.py to avoid circular imports)
# ============================================================================
# ProcessingStatus, ExtractionMethod, Language, FileFormat
# are defined in models.py and imported in __init__.py


# ============================================================================
# VALIDATION RULES
# ============================================================================

class ValidationRules:
    """Data validation rules"""
    
    # Birth year validation
    MIN_BIRTH_YEAR = 1940
    MAX_BIRTH_YEAR = 2010
    
    # Name validation
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    
    # Text length validation
    MIN_PROFILE_LENGTH = 50
    MAX_PROFILE_LENGTH = 1000
    MIN_DESCRIPTION_LENGTH = 10
    
    # Required fields
    REQUIRED_FIELDS = ['name', 'location', 'birth_year', 'work_experience', 'education']


# ============================================================================
# FILE PATHS (relative to project root)
# ============================================================================

class Paths:
    """Standard file paths"""
    
    # Base directories
    NETWORK_FOLDER = r"C:\Users\RudoJockinSynergiepr\Synergie PM\Netwerk - Documenten"
    CV_AUTOMATION_ROOT = r"C:\Users\RudoJockinSynergiepr\Synergie PM\CV Automation"
    
    # Data directories
    DATA_DIR = "data"
    DATA_ANALYSIS = "data/analysis"
    DATA_PROCESSING = "data/processing"
    DATA_TEMPLATES = "data/templates"
    
    # Database
    DATABASE_DIR = "database"
    DATABASE_FILE = "database/cv_automation.db"
    
    # Logs
    LOGS_DIR = "logs"
    APP_LOG = "logs/app.log"
    ERROR_LOG = "logs/error.log"
    PROCESSING_LOG = "logs/processing.log"
    
    # Output
    OUTPUT_DIR = "output"
    BACKUP_DIR = "output/backups"


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class LogConfig:
    """Logging configuration"""
    
    # Log format (with timestamps as per user preference)
    LOG_FORMAT = "[{time:YYYY-MM-DD HH:mm:ss}] [{level}] [{name}] {message}"
    
    # Log levels
    LEVEL_DEBUG = "DEBUG"
    LEVEL_INFO = "INFO"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"
    LEVEL_CRITICAL = "CRITICAL"
    
    # Default level
    DEFAULT_LEVEL = "INFO"
    
    # File rotation
    ROTATION = "10 MB"
    RETENTION = "30 days"


# ============================================================================
# TEMPLATE SPECIFICATIONS
# ============================================================================

class TemplateSpecs:
    """Complete template specifications based on reverse engineering"""
    
    # Document setup
    PAGE_WIDTH = Inches(8.27)
    PAGE_HEIGHT = Inches(11.69)
    MARGIN_TOP = Inches(1.69)
    MARGIN_BOTTOM = Inches(1.18)
    MARGIN_LEFT = Inches(0.75)
    MARGIN_RIGHT = Inches(0.75)
    
    # Font defaults
    DEFAULT_FONT = SynergieFonts.PRIMARY
    DEFAULT_SIZE = FontSizes.BODY_TEXT
    
    # Color defaults
    DEFAULT_COLOR = SynergieColors.BLACK
    HEADER_COLOR = SynergieColors.SECTION_HEADER
    
    # Table specifications
    TABLE_DATE_COLUMN = Inches(0.89)
    TABLE_CONTENT_COLUMN = Inches(5.88)
    TABLE_SINGLE_COLUMN = Inches(6.76)
    
    # Styles
    NAME_STYLE = "Headline"  # From reverse engineering
    BODY_STYLE = "Normal"
    
    # Spacing
    PARAGRAPH_SPACING_BEFORE = Pt(0)
    PARAGRAPH_SPACING_AFTER = Pt(0)
    LINE_SPACING = 1.0  # Single spacing


# ============================================================================
# ERROR MESSAGES
# ============================================================================

class ErrorMessages:
    """Standard error messages"""
    
    FILE_NOT_FOUND = "File not found: {path}"
    EXTRACTION_FAILED = "Text extraction failed for {filename}"
    PARSING_FAILED = "Section parsing failed: {reason}"
    VALIDATION_FAILED = "Data validation failed: {errors}"
    GENERATION_FAILED = "Resumé generation failed: {reason}"
    OCR_REQUIRED = "File requires OCR processing: {filename}"
    UNSUPPORTED_FORMAT = "Unsupported file format: {extension}"


# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

class SuccessMessages:
    """Standard success messages"""
    
    EXTRACTION_SUCCESS = "Text extracted successfully: {char_count} characters"
    PARSING_SUCCESS = "Sections parsed successfully: {section_count} sections found"
    GENERATION_SUCCESS = "Resumé generated: {filename}"
    VALIDATION_SUCCESS = "Validation passed with confidence: {score:.2f}"


# ============================================================================
# SYSTEM METADATA
# ============================================================================

class SystemInfo:
    """System metadata"""
    
    VERSION = "1.0.0"
    NAME = "CV Automation System"
    DESCRIPTION = "Automated CV to Resumé Generation for Synergie PM"
    
    # Analysis metadata
    TOTAL_CVS_ANALYZED = 949
    TOTAL_RESUMES_ANALYZED = 539
    ANALYSIS_DATE = "2025-10-01"
    
    # Expected performance
    EXPECTED_SUCCESS_RATE = 0.937  # 93.7%
    EXPECTED_OCR_RATE = 0.063      # 6.3%
    EXPECTED_AUTOMATION_RATE = 0.80  # 80%


# ============================================================================
# QUALITY THRESHOLDS
# ============================================================================

class QualityThresholds:
    """Quality control thresholds"""
    
    # Minimum requirements
    MIN_SECTIONS_REQUIRED = 3       # At least 3 critical sections
    MIN_WORK_EXPERIENCE = 1         # At least 1 work experience
    MIN_EDUCATION = 1               # At least 1 education entry
    
    # Confidence thresholds
    AUTO_APPROVE_CONFIDENCE = 0.9
    QUICK_REVIEW_CONFIDENCE = 0.7
    DETAILED_REVIEW_CONFIDENCE = 0.5
    MANUAL_PROCESSING_CONFIDENCE = 0.3


# ============================================================================
# PAGE SETUP (From analysis of 539 Resumés)
# ============================================================================

class SynergiePageSetup:
    """Page setup specifications"""
    
    # A4 page dimensions (in inches)
    PAGE_WIDTH = 8.27  # A4 width
    PAGE_HEIGHT = 11.69  # A4 height
    
    # Margins (in inches)
    MARGIN_TOP = 0.5
    MARGIN_BOTTOM = 0.5
    MARGIN_LEFT = 0.5
    MARGIN_RIGHT = 0.5


class SynergieTableSpecs:
    """Table specifications"""
    
    # Column widths (in inches)
    DATE_COLUMN_WIDTH = 0.89
    CONTENT_COLUMN_WIDTH = 5.88
    
    # Table alignment
    TABLE_ALIGNMENT = "left"

