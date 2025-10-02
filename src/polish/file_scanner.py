#!/usr/bin/env python3
"""
File Scanner - Robust file discovery and validation
Generic file scanning with comprehensive validation and metadata extraction
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Generator, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.core import CVFile, FileFormat, Timer


class ScanStatus(str, Enum):
    """File scan status"""
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    INVALID = "invalid"
    DUPLICATE = "duplicate"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileMetadata:
    """Comprehensive file metadata"""
    file_path: str
    file_name: str
    file_size: int
    file_format: FileFormat
    mime_type: str
    created_date: datetime
    modified_date: datetime
    checksum: str
    scan_status: ScanStatus = ScanStatus.DISCOVERED
    validation_errors: List[str] = field(default_factory=list)
    processing_priority: int = 5  # 1=highest, 10=lowest
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)


class FileScanner:
    """
    Generic file scanner with comprehensive validation
    
    Features:
    - Recursive directory scanning
    - File format detection
    - Duplicate detection via checksum
    - Metadata extraction
    - Validation rules engine
    - Progress tracking
    - Error recovery
    """
    
    def __init__(self, config: Dict[str, any] = None):
        """Initialize file scanner with configuration"""
        self.config = config or {}
        
        # Scan configuration
        self.supported_formats = self.config.get('supported_formats', ['.pdf', '.docx', '.doc'])
        self.max_file_size = self.config.get('max_file_size', 50 * 1024 * 1024)  # 50MB
        self.min_file_size = self.config.get('min_file_size', 1024)  # 1KB
        self.scan_depth = self.config.get('scan_depth', 10)  # Max directory depth
        self.exclude_patterns = self.config.get('exclude_patterns', ['.git', '__pycache__', 'node_modules'])
        
        # Validation rules
        self.validation_rules = self.config.get('validation_rules', {})
        
        # State tracking
        self.scanned_files: Dict[str, FileMetadata] = {}
        self.duplicate_files: Dict[str, List[str]] = {}  # checksum -> [file_paths]
        self.scan_stats = {
            'total_discovered': 0,
            'total_validated': 0,
            'total_invalid': 0,
            'total_duplicates': 0,
            'scan_start_time': None,
            'scan_end_time': None
        }
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> Generator[FileMetadata, None, None]:
        """
        Scan directory for files with comprehensive validation
        
        Args:
            directory_path: Path to scan
            recursive: Whether to scan subdirectories
            
        Yields:
            FileMetadata objects for each discovered file
        """
        self.scan_stats['scan_start_time'] = datetime.now()
        self._log(f"Starting file scan of: {directory_path}")
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Scan files
            for file_path in self._get_files_to_scan(directory, recursive):
                try:
                    metadata = self._extract_file_metadata(file_path)
                    
                    # Validate file
                    if self._validate_file(metadata):
                        metadata.scan_status = ScanStatus.VALIDATED
                        self.scanned_files[str(file_path)] = metadata
                        self.scan_stats['total_validated'] += 1
                        yield metadata
                    else:
                        metadata.scan_status = ScanStatus.INVALID
                        self.scan_stats['total_invalid'] += 1
                        self._log(f"Invalid file: {file_path} - {metadata.validation_errors}", "WARNING")
                
                except Exception as e:
                    self._log(f"Error processing file {file_path}: {str(e)}", "ERROR")
                    continue
            
            self.scan_stats['scan_end_time'] = datetime.now()
            self._log(f"Scan completed: {self.scan_stats['total_validated']} valid files found")
            
        except Exception as e:
            self._log(f"Directory scan failed: {str(e)}", "ERROR")
            raise
    
    def _get_files_to_scan(self, directory: Path, recursive: bool) -> Generator[Path, None, None]:
        """Get all files to scan based on configuration"""
        if recursive:
            # Recursive scan with depth limit
            for root, dirs, files in os.walk(directory):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.exclude_patterns)]
                
                # Check depth
                depth = root.replace(str(directory), '').count(os.sep)
                if depth >= self.scan_depth:
                    dirs.clear()
                    continue
                
                for file in files:
                    file_path = Path(root) / file
                    if self._should_scan_file(file_path):
                        yield file_path
        else:
            # Non-recursive scan
            for file_path in directory.iterdir():
                if file_path.is_file() and self._should_scan_file(file_path):
                    yield file_path
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned based on configuration"""
        # Check file extension
        if file_path.suffix.lower() not in self.supported_formats:
            return False
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size < self.min_file_size or file_size > self.max_file_size:
                return False
        except OSError:
            return False
        
        return True
    
    def _extract_file_metadata(self, file_path: Path) -> FileMetadata:
        """Extract comprehensive metadata from file"""
        stat = file_path.stat()
        
        # Calculate checksum for duplicate detection
        checksum = self._calculate_checksum(file_path)
        
        # Detect file format
        file_format = FileFormat.from_extension(file_path.suffix.lower())
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or 'application/octet-stream'
        
        # Extract additional metadata
        metadata = {
            'directory': str(file_path.parent),
            'relative_path': str(file_path.relative_to(file_path.parent.parent)) if file_path.parent.parent else str(file_path.name),
            'extension': file_path.suffix.lower(),
            'stem': file_path.stem,
        }
        
        return FileMetadata(
            file_path=str(file_path),
            file_name=file_path.name,
            file_size=stat.st_size,
            file_format=file_format,
            mime_type=mime_type,
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
            checksum=checksum,
            metadata=metadata
        )
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for duplicate detection"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return "unknown"
    
    def _validate_file(self, metadata: FileMetadata) -> bool:
        """Validate file against all rules"""
        metadata.validation_errors.clear()
        
        # Basic validation
        if not self._validate_file_size(metadata):
            metadata.validation_errors.append("File size outside acceptable range")
        
        if not self._validate_file_format(metadata):
            metadata.validation_errors.append("Unsupported file format")
        
        if not self._validate_file_access(metadata):
            metadata.validation_errors.append("File cannot be accessed")
        
        # Custom validation rules
        for rule_name, rule_func in self.validation_rules.items():
            try:
                if not rule_func(metadata):
                    metadata.validation_errors.append(f"Failed validation rule: {rule_name}")
            except Exception as e:
                metadata.validation_errors.append(f"Validation rule {rule_name} error: {str(e)}")
        
        # Check for duplicates
        if self._is_duplicate(metadata):
            metadata.validation_errors.append("Duplicate file detected")
            self.scan_stats['total_duplicates'] += 1
        
        return len(metadata.validation_errors) == 0
    
    def _validate_file_size(self, metadata: FileMetadata) -> bool:
        """Validate file size"""
        return self.min_file_size <= metadata.file_size <= self.max_file_size
    
    def _validate_file_format(self, metadata: FileMetadata) -> bool:
        """Validate file format"""
        return metadata.file_format != FileFormat.UNKNOWN
    
    def _validate_file_access(self, metadata: FileMetadata) -> bool:
        """Validate file can be accessed"""
        try:
            with open(metadata.file_path, 'rb') as f:
                f.read(1)  # Try to read first byte
            return True
        except Exception:
            return False
    
    def _is_duplicate(self, metadata: FileMetadata) -> bool:
        """Check if file is a duplicate"""
        if metadata.checksum in self.duplicate_files:
            self.duplicate_files[metadata.checksum].append(metadata.file_path)
            return True
        else:
            self.duplicate_files[metadata.checksum] = [metadata.file_path]
            return False
    
    def get_scan_statistics(self) -> Dict[str, any]:
        """Get comprehensive scan statistics"""
        duration = None
        if self.scan_stats['scan_start_time'] and self.scan_stats['scan_end_time']:
            duration = (self.scan_stats['scan_end_time'] - self.scan_stats['scan_start_time']).total_seconds()
        
        return {
            'scan_duration_seconds': duration,
            'total_files_discovered': len(self.scanned_files),
            'valid_files': self.scan_stats['total_validated'],
            'invalid_files': self.scan_stats['total_invalid'],
            'duplicate_files': self.scan_stats['total_duplicates'],
            'duplicate_groups': len([group for group in self.duplicate_files.values() if len(group) > 1]),
            'file_formats': self._get_format_distribution(),
            'file_sizes': self._get_size_distribution(),
            'scan_configuration': {
                'supported_formats': self.supported_formats,
                'max_file_size': self.max_file_size,
                'min_file_size': self.min_file_size,
                'scan_depth': self.scan_depth
            }
        }
    
    def _get_format_distribution(self) -> Dict[str, int]:
        """Get distribution of file formats"""
        distribution = {}
        for metadata in self.scanned_files.values():
            format_name = metadata.file_format.value
            distribution[format_name] = distribution.get(format_name, 0) + 1
        return distribution
    
    def _get_size_distribution(self) -> Dict[str, int]:
        """Get distribution of file sizes"""
        size_ranges = {
            'small (<1MB)': 0,
            'medium (1-10MB)': 0,
            'large (10-50MB)': 0,
            'very_large (>50MB)': 0
        }
        
        for metadata in self.scanned_files.values():
            size_mb = metadata.file_size / (1024 * 1024)
            if size_mb < 1:
                size_ranges['small (<1MB)'] += 1
            elif size_mb < 10:
                size_ranges['medium (1-10MB)'] += 1
            elif size_mb < 50:
                size_ranges['large (10-50MB)'] += 1
            else:
                size_ranges['very_large (>50MB)'] += 1
        
        return size_ranges
    
    def get_files_by_status(self, status: ScanStatus) -> List[FileMetadata]:
        """Get all files with specific status"""
        return [metadata for metadata in self.scanned_files.values() if metadata.scan_status == status]
    
    def get_duplicate_files(self) -> Dict[str, List[str]]:
        """Get all duplicate file groups"""
        return {checksum: files for checksum, files in self.duplicate_files.items() if len(files) > 1}
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [FileScanner] {message}")
