#!/usr/bin/env python3
"""
Custom Exceptions - Exception hierarchy for CV Automation System
Provides specific exception types for better error handling
"""


class CVAutomationException(Exception):
    """Base exception for all CV Automation errors"""
    pass


# ============================================================================
# INPUT LAYER EXCEPTIONS
# ============================================================================

class InputException(CVAutomationException):
    """Base exception for input layer errors"""
    pass


class FileNotFoundException(InputException):
    """File not found in expected location"""
    pass


class InvalidFileFormatException(InputException):
    """File format is not supported"""
    pass


class FileCorruptedException(InputException):
    """File appears to be corrupted"""
    pass


class FileTooLargeException(InputException):
    """File exceeds maximum size limit"""
    pass


class FileTooSmallException(InputException):
    """File is suspiciously small (likely empty)"""
    pass


# ============================================================================
# EXTRACTION LAYER EXCEPTIONS
# ============================================================================

class ExtractionException(CVAutomationException):
    """Base exception for extraction layer errors"""
    pass


class TextExtractionFailedException(ExtractionException):
    """Failed to extract text from file"""
    pass


class OCRRequiredException(ExtractionException):
    """File requires OCR processing (image-based PDF)"""
    pass


class OCRFailedException(ExtractionException):
    """OCR processing failed"""
    pass


class UnsupportedDocumentException(ExtractionException):
    """Document type is not supported"""
    pass


# ============================================================================
# PARSING LAYER EXCEPTIONS
# ============================================================================

class ParsingException(CVAutomationException):
    """Base exception for parsing errors"""
    pass


class SectionNotFoundException(ParsingException):
    """Required section not found in CV"""
    pass


class DateParsingException(ParsingException):
    """Failed to parse date from text"""
    pass


class LanguageDetectionException(ParsingException):
    """Failed to detect document language"""
    pass


class NameExtractionException(ParsingException):
    """Failed to extract person's name"""
    pass


# ============================================================================
# VALIDATION LAYER EXCEPTIONS
# ============================================================================

class ValidationException(CVAutomationException):
    """Base exception for validation errors"""
    pass


class MissingRequiredFieldException(ValidationException):
    """Required field is missing from extracted data"""
    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Required field missing: {field_name}")


class InvalidDataException(ValidationException):
    """Extracted data is invalid"""
    pass


class LowConfidenceException(ValidationException):
    """Confidence score too low for automatic processing"""
    def __init__(self, score: float, threshold: float):
        self.score = score
        self.threshold = threshold
        super().__init__(f"Confidence score {score:.2f} below threshold {threshold:.2f}")


# ============================================================================
# GENERATION LAYER EXCEPTIONS
# ============================================================================

class GenerationException(CVAutomationException):
    """Base exception for generation errors"""
    pass


class TemplateLoadException(GenerationException):
    """Failed to load template"""
    pass


class TableCreationException(GenerationException):
    """Failed to create table in document"""
    pass


class FormattingException(GenerationException):
    """Failed to apply formatting"""
    pass


class PDFConversionException(GenerationException):
    """Failed to convert DOCX to PDF"""
    pass


# ============================================================================
# OUTPUT LAYER EXCEPTIONS
# ============================================================================

class OutputException(CVAutomationException):
    """Base exception for output errors"""
    pass


class FileSaveException(OutputException):
    """Failed to save file"""
    pass


class FileAlreadyExistsException(OutputException):
    """File already exists and overwrite not permitted"""
    pass


class PermissionException(OutputException):
    """Insufficient permissions to write file"""
    pass


# ============================================================================
# DATABASE EXCEPTIONS
# ============================================================================

class DatabaseException(CVAutomationException):
    """Base exception for database errors"""
    pass


class RecordNotFoundException(DatabaseException):
    """Database record not found"""
    pass


class DuplicateRecordException(DatabaseException):
    """Attempt to create duplicate record"""
    pass


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================

class ConfigurationException(CVAutomationException):
    """Base exception for configuration errors"""
    pass


class MissingConfigException(ConfigurationException):
    """Required configuration is missing"""
    pass


class InvalidConfigException(ConfigurationException):
    """Configuration value is invalid"""
    pass

