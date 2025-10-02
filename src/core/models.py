#!/usr/bin/env python3
"""
Core Data Models - Data structures for CV Automation System
Defines all data models using Python dataclasses with type hints
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

# Note: Import constants after they're needed to avoid circular import
# These will be imported when the module is fully loaded


# ============================================================================
# ENUMS (Define here to avoid circular imports)
# ============================================================================

class ProcessingStatus(str, Enum):
    """CV processing status"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"
    MANUAL_PROCESSING = "manual_processing"


class ExtractionMethod(str, Enum):
    """Text extraction methods"""
    DOCX = "docx"
    PDF = "pdf"
    OCR = "ocr"
    MANUAL = "manual"


class Language(str, Enum):
    """Supported languages"""
    DUTCH = "Dutch"
    ENGLISH = "English"
    MIXED = "Mixed (Dutch/English)"
    UNKNOWN = "Unknown"


class FileFormat(str, Enum):
    """Supported file formats"""
    PDF = ".pdf"
    DOCX = ".docx"
    DOC = ".doc"
    UNKNOWN = ".unknown"
    
    @classmethod
    def from_extension(cls, extension: str) -> 'FileFormat':
        """Convert file extension to FileFormat enum"""
        extension = extension.lower()
        if extension == '.pdf':
            return cls.PDF
        elif extension == '.docx':
            return cls.DOCX
        elif extension == '.doc':
            return cls.DOC
        else:
            return cls.UNKNOWN


class ReviewPriority(int, Enum):
    """Review queue priority levels"""
    CRITICAL = 1
    HIGH = 3
    MEDIUM = 5
    LOW = 7
    INFORMATIONAL = 10


# ============================================================================
# FILE MODELS
# ============================================================================

@dataclass
class CVFile:
    """Represents a CV file in the system"""
    id: str  # Unique identifier (e.g., hash or UUID)
    person_name: str  # Folder name (e.g., "Smit, Ronald")
    file_path: str  # Full path to CV file
    file_name: str  # Just the filename
    file_format: FileFormat
    file_size: int  # Bytes
    
    # Processing metadata
    status: ProcessingStatus = ProcessingStatus.PENDING
    added_date: datetime = field(default_factory=datetime.now)
    processed_date: Optional[datetime] = None
    
    # Processing results
    confidence_score: float = 0.0
    needs_review: bool = False
    review_reason: Optional[str] = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def __str__(self):
        return f"CVFile({self.person_name}: {self.file_name})"


# ============================================================================
# EXTRACTION MODELS
# ============================================================================

@dataclass
class ExtractionResult:
    """Result of text extraction from a CV file"""
    success: bool
    text: str
    method: Optional[ExtractionMethod] = None
    
    # Metadata
    page_count: int = 0
    char_count: int = 0
    word_count: int = 0
    extraction_time: float = 0.0  # seconds
    
    # Quality indicators
    has_selectable_text: bool = True
    ocr_confidence: Optional[float] = None  # For OCR extractions
    
    # Error information
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.text:
            self.char_count = len(self.text)
            self.word_count = len(self.text.split())


# ============================================================================
# PERSONAL INFORMATION
# ============================================================================

@dataclass
class PersonalInfo:
    """Personal information extracted from CV"""
    # Required for Resumé
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    location: Optional[str] = None  # City only (privacy)
    birth_year: Optional[int] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Additional information
    nationality: Optional[str] = None
    driver_license: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    
    # Validation and metadata
    confidence: float = 0.0
    language: Language = Language.UNKNOWN
    
    # Legacy fields
    full_address: Optional[str] = None
    birth_date: Optional[date] = None
    marital_status: Optional[str] = None
    
    # Validation
    def is_valid(self) -> bool:
        """Check if required fields are present"""
        return all([
            self.full_name,
            self.first_name,
            self.last_name,
            self.location,
            self.birth_year,
            1940 <= self.birth_year <= 2010
        ])


# ============================================================================
# DATE MODELS
# ============================================================================

@dataclass
class DateRange:
    """Represents a date range"""
    start: str  # YYYY or YYYY-MM format
    end: Optional[str] = None  # YYYY, YYYY-MM, or None for current
    is_current: bool = False  # True if end is "heden"/"present"
    
    # Original text (for debugging)
    original_text: Optional[str] = None
    
    def to_resume_format(self) -> str:
        """Convert to standard Resumé format"""
        if self.is_current:
            return f"{self.start} – heden"
        elif self.end:
            return f"{self.start} – {self.end}"
        else:
            return self.start
    
    def __str__(self):
        return self.to_resume_format()


# ============================================================================
# WORK EXPERIENCE MODELS
# ============================================================================

@dataclass
class Project:
    """A project within a work experience entry"""
    name: str
    client: Optional[str] = None
    period: Optional[DateRange] = None
    role: str = ""
    responsibilities: List[str] = field(default_factory=list)
    
    # Additional details
    description: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    team_size: Optional[int] = None


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
    responsibilities: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    duration_months: Optional[int] = None
    confidence: float = 0.0
    original_text: str = ""
    
    # Legacy fields for compatibility
    job_title: Optional[str] = None
    period: Optional[DateRange] = None
    general_responsibilities: List[str] = field(default_factory=list)
    employment_type: Optional[str] = None
    
    def __str__(self):
        if self.company and self.position:
            return f"{self.position} bij {self.company}"
        elif self.company:
            return self.company
        else:
            return "Work Experience"


# ============================================================================
# EDUCATION MODELS
# ============================================================================

@dataclass
class Education:
    """Education entry"""
    degree: str
    institution: str
    
    # Dates
    period: Optional[DateRange] = None
    graduation_year: Optional[int] = None
    
    # Additional details
    field_of_study: Optional[str] = None
    honors: Optional[str] = None
    grade: Optional[str] = None
    
    def __str__(self):
        if self.period:
            return f"{self.degree} - {self.institution} ({self.period})"
        return f"{self.degree} - {self.institution}"


@dataclass
class Course:
    """Course/training/certification entry"""
    name: str
    year: int
    
    # Additional details
    provider: Optional[str] = None
    duration: Optional[str] = None
    certificate_number: Optional[str] = None
    
    def __str__(self):
        return f"{self.name} ({self.year})"


# ============================================================================
# COMPLETE CV DATA MODEL
# ============================================================================

@dataclass
class CVData:
    """Complete structured data extracted from a CV"""
    # Identification
    cv_id: str
    person_name: str
    
    # Core data
    personal_info: PersonalInfo
    work_experience: List[WorkExperience]
    education: List[Education]
    
    # Optional data
    profile: Optional[str] = None
    courses: List[Course] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    software: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    # Metadata
    language: Language = Language.DUTCH
    extraction_method: ExtractionMethod = ExtractionMethod.DOCX
    extraction_date: datetime = field(default_factory=datetime.now)
    
    # Source
    source_file: str = ""
    raw_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'cv_id': self.cv_id,
            'person_name': self.person_name,
            'personal_info': {
                'full_name': self.personal_info.full_name,
                'first_name': self.personal_info.first_name,
                'last_name': self.personal_info.last_name,
                'location': self.personal_info.location,
                'birth_year': self.personal_info.birth_year,
            },
            'profile': self.profile,
            'work_experience': [
                {
                    'company': we.company,
                    'period': str(we.period),
                    'job_title': we.job_title,
                    'projects': [{'name': p.name, 'role': p.role} for p in we.projects]
                }
                for we in self.work_experience
            ],
            'education': [
                {
                    'degree': edu.degree,
                    'institution': edu.institution,
                    'period': str(edu.period) if edu.period else None
                }
                for edu in self.education
            ],
            'courses': [{'name': c.name, 'year': c.year} for c in self.courses],
            'language': self.language.value,
        }


# ============================================================================
# RESUMÉ DATA MODEL (Simplified for generation)
# ============================================================================

@dataclass
class ResumeData:
    """Structured data for Resumé generation (privacy-compliant)"""
    # Header (ONLY these 3 items)
    name: str
    location: str  # City only, no full address
    birth_year: int  # Year only, no full birthdate
    
    # Optional profile
    profile: Optional[str] = None
    
    # Core sections
    work_experience: List[WorkExperience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    courses: List[Course] = field(default_factory=list)
    
    # Optional sections (rarely used in Resumés)
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    
    # Metadata
    language: Language = Language.DUTCH
    generation_date: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_cv_data(cls, cv_data: CVData) -> 'ResumeData':
        """Create ResumeData from CVData (applies privacy filters)"""
        return cls(
            name=cv_data.personal_info.full_name,
            location=cv_data.personal_info.location,
            birth_year=cv_data.personal_info.birth_year,
            profile=cv_data.profile,
            work_experience=cv_data.work_experience,
            education=cv_data.education,
            courses=cv_data.courses,
            skills=cv_data.skills[:10] if cv_data.skills else [],  # Limit to top 10
            languages=cv_data.languages,
            language=cv_data.language,
        )


# ============================================================================
# VALIDATION MODELS
# ============================================================================

@dataclass
class ValidationError:
    """Represents a validation error"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    confidence_score: float = 0.0
    
    def add_error(self, field: str, message: str):
        """Add validation error"""
        self.errors.append(ValidationError(field, message, "error"))
        self.is_valid = False
    
    def add_warning(self, field: str, message: str):
        """Add validation warning"""
        self.warnings.append(ValidationError(field, message, "warning"))
    
    def get_summary(self) -> str:
        """Get validation summary"""
        if self.is_valid:
            if self.warnings:
                return f"Valid with {len(self.warnings)} warnings (confidence: {self.confidence_score:.2f})"
            return f"Valid (confidence: {self.confidence_score:.2f})"
        return f"Invalid: {len(self.errors)} errors, {len(self.warnings)} warnings"


# ============================================================================
# PROCESSING RESULT MODELS
# ============================================================================

@dataclass
class ProcessingStep:
    """Represents a single processing step"""
    step_name: str
    status: str  # started, completed, failed
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0  # seconds
    error: Optional[str] = None
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark step as completed"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "completed" if success else "failed"
        if error:
            self.error = error


@dataclass
class ProcessingResult:
    """Complete result of CV → Resumé processing"""
    cv_id: str
    person_name: str
    success: bool
    
    # Generated files
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    
    # Quality metrics
    confidence_score: float = 0.0
    validation_result: Optional[ValidationResult] = None
    
    # Processing metadata
    processing_time: float = 0.0  # Total seconds
    processing_steps: List[ProcessingStep] = field(default_factory=list)
    
    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Review information
    needs_review: bool = False
    review_reason: Optional[str] = None
    review_priority: ReviewPriority = ReviewPriority.MEDIUM
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_step(self, step_name: str) -> ProcessingStep:
        """Add a new processing step"""
        step = ProcessingStep(
            step_name=step_name,
            status="started",
            start_time=datetime.now()
        )
        self.processing_steps.append(step)
        return step
    
    def mark_complete(self, success: bool = True):
        """Mark processing as complete"""
        self.completed_at = datetime.now()
        self.success = success
        self.processing_time = (self.completed_at - self.started_at).total_seconds()


# ============================================================================
# REVIEW QUEUE MODELS
# ============================================================================

@dataclass
class ReviewItem:
    """Item in the review queue"""
    id: str
    cv_id: str
    person_name: str
    priority: ReviewPriority
    reason: str
    
    # Files to review
    cv_file_path: str
    resume_docx_path: Optional[str] = None
    resume_pdf_path: Optional[str] = None
    
    # Extracted data
    extracted_data: Optional[Dict[str, Any]] = None
    
    # Review metadata
    status: str = "pending"  # pending, in_review, completed, rejected
    assigned_to: Optional[str] = None
    added_date: datetime = field(default_factory=datetime.now)
    reviewed_date: Optional[datetime] = None
    
    # Review results
    approved: bool = False
    corrections: Optional[Dict[str, Any]] = None
    reviewer_notes: Optional[str] = None


# ============================================================================
# BATCH PROCESSING MODELS
# ============================================================================

@dataclass
class BatchJob:
    """Represents a batch processing job"""
    id: str
    total_items: int
    
    # Progress tracking
    completed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    
    # Status
    status: str = "pending"  # pending, running, paused, completed, failed
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # Performance
    average_time_per_item: float = 0.0
    items_per_minute: float = 0.0
    
    # Results
    successful_cv_ids: List[str] = field(default_factory=list)
    failed_cv_ids: List[str] = field(default_factory=list)
    
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_items == 0:
            return 0.0
        processed = self.completed_items + self.failed_items + self.skipped_items
        return (processed / self.total_items) * 100
    
    def eta_minutes(self) -> Optional[float]:
        """Estimate time to completion in minutes"""
        if self.average_time_per_item == 0 or self.total_items == 0:
            return None
        remaining = self.total_items - (self.completed_items + self.failed_items + self.skipped_items)
        return (remaining * self.average_time_per_item) / 60


# ============================================================================
# SECTION MODELS
# ============================================================================

@dataclass
class Section:
    """Represents a section in a CV"""
    name: str  # Section type (e.g., "Work Experience")
    content: str  # Raw text content
    start_line: int  # Line number where section starts
    end_line: int  # Line number where section ends
    confidence: float = 1.0  # Confidence in section detection


@dataclass
class ParsedCV:
    """CV with identified sections"""
    cv_id: str
    language: Language
    
    # Identified sections
    sections: List[Section] = field(default_factory=list)
    
    # Parsing metadata
    total_lines: int = 0
    sections_found: int = 0
    parsing_confidence: float = 0.0
    
    def get_section(self, section_name: str) -> Optional[Section]:
        """Get section by name"""
        for section in self.sections:
            if section.name.lower() == section_name.lower():
                return section
        return None


# ============================================================================
# METRICS MODELS
# ============================================================================

@dataclass
class SystemMetrics:
    """System performance metrics"""
    # Counters
    total_processed: int = 0
    total_successful: int = 0
    total_failed: int = 0
    total_in_review: int = 0
    
    # Performance
    average_processing_time: float = 0.0
    total_processing_time: float = 0.0
    
    # Quality
    average_confidence_score: float = 0.0
    extraction_success_rate: float = 0.0
    generation_success_rate: float = 0.0
    
    # Current status
    files_in_queue: int = 0
    files_processing: int = 0
    review_queue_size: int = 0
    
    # Timestamp
    last_updated: datetime = field(default_factory=datetime.now)
    
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_processed == 0:
            return 0.0
        return (self.total_successful / self.total_processed) * 100


# ============================================================================
# CONFIGURATION MODEL
# ============================================================================

@dataclass
class SystemConfig:
    """System configuration"""
    # Paths
    network_folder: str
    output_folder: str
    database_path: str
    log_dir: str
    
    # Processing settings
    batch_size: int = 10
    max_workers: int = 4
    enable_ocr: bool = True
    enable_parallel: bool = True
    
    # Quality settings
    min_confidence_auto_approve: float = 0.9
    min_confidence_quick_review: float = 0.7
    
    # Feature flags
    save_intermediate_results: bool = True
    create_backups: bool = True
    generate_pdf: bool = True
    
    # Timeouts
    extraction_timeout: int = 60
    generation_timeout: int = 30
    ocr_timeout: int = 120


# ============================================================================
# UTILITY MODELS
# ============================================================================

@dataclass
class FileMetadata:
    """File metadata and statistics"""
    path: str
    name: str
    size: int
    extension: str
    created_date: datetime
    modified_date: datetime
    
    # Checksums (for integrity verification)
    md5_hash: Optional[str] = None
    sha256_hash: Optional[str] = None


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    component: str  # Which component logged this
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{self.level}] [{self.component}] {self.message}"

