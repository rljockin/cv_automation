#!/usr/bin/env python3
"""
Output Manager - File saving and organization
Generic output management system with file organization, versioning, and backup
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.core import CVData, CVFile


class OutputStatus(str, Enum):
    """Output file status"""
    CREATED = "created"
    UPDATED = "updated"
    FAILED = "failed"
    BACKED_UP = "backed_up"
    ARCHIVED = "archived"


class FileType(str, Enum):
    """Output file types"""
    DOCX = "docx"
    PDF = "pdf"
    JSON = "json"
    LOG = "log"
    BACKUP = "backup"
    ARCHIVE = "archive"


@dataclass
class OutputFile:
    """Output file metadata"""
    id: str
    original_file: CVFile
    output_path: str
    file_type: FileType
    status: OutputStatus
    created_at: datetime = field(default_factory=datetime.now)
    file_size: int = 0
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    backup_path: Optional[str] = None
    archive_path: Optional[str] = None


@dataclass
class OutputConfiguration:
    """Output configuration"""
    base_output_dir: str = "output"
    organize_by_date: bool = True
    organize_by_person: bool = True
    create_backups: bool = True
    backup_retention_days: int = 30
    archive_old_files: bool = True
    archive_after_days: int = 90
    file_naming_pattern: str = "{person_name}_{date}_{type}"
    create_metadata_files: bool = True
    compression_enabled: bool = False


class OutputManager:
    """
    Generic output management system with comprehensive file organization
    
    Features:
    - Intelligent file organization
    - Automatic backup and versioning
    - File naming and metadata management
    - Archive and cleanup procedures
    - Output validation and integrity checks
    - Progress tracking and reporting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize output manager"""
        self.config = config or {}
        self.output_config = OutputConfiguration(**self.config.get('output_config', {}))
        
        # Output state
        self.output_files: Dict[str, OutputFile] = {}
        self.output_statistics = {
            'total_files_created': 0,
            'total_files_updated': 0,
            'total_files_failed': 0,
            'total_backups_created': 0,
            'total_archives_created': 0,
            'total_storage_used': 0
        }
        
        # Directory structure
        self.base_dir = Path(self.output_config.base_output_dir)
        self._ensure_directory_structure()
    
    def save_resume(self, cv_file: CVFile, cv_data: CVData, 
                   docx_content: bytes, pdf_content: Optional[bytes] = None,
                   metadata: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Save resume files with proper organization
        
        Args:
            cv_file: Original CV file
            cv_data: Parsed CV data
            docx_content: DOCX file content
            pdf_content: PDF file content (optional)
            metadata: Additional metadata
            
        Returns:
            Tuple of (docx_path, pdf_path)
        """
        try:
            # Generate output paths
            person_name = self._sanitize_name(cv_data.person_name or "Unknown")
            date_str = datetime.now().strftime('%Y%m%d')
            
            # Create directory structure
            output_dir = self._create_output_directory(person_name, date_str)
            
            # Generate file names
            docx_filename = self._generate_filename(person_name, date_str, "resume", FileType.DOCX)
            pdf_filename = self._generate_filename(person_name, date_str, "resume", FileType.PDF)
            
            # Save DOCX file
            docx_path = output_dir / docx_filename
            with open(docx_path, 'wb') as f:
                f.write(docx_content)
            
            # Save PDF file if provided
            pdf_path = None
            if pdf_content:
                pdf_path = output_dir / pdf_filename
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_content)
            
            # Create metadata file
            if self.output_config.create_metadata_files:
                metadata_path = self._save_metadata(output_dir, cv_file, cv_data, metadata)
            
            # Create output file records
            docx_output = self._create_output_record(
                cv_file, str(docx_path), FileType.DOCX, OutputStatus.CREATED, metadata
            )
            self.output_files[docx_output.id] = docx_output
            
            if pdf_path:
                pdf_output = self._create_output_record(
                    cv_file, str(pdf_path), FileType.PDF, OutputStatus.CREATED, metadata
                )
                self.output_files[pdf_output.id] = pdf_output
            
            # Create backup if configured
            if self.output_config.create_backups:
                self._create_backup(docx_output)
                if pdf_path:
                    self._create_backup(pdf_output)
            
            # Update statistics
            self.output_statistics['total_files_created'] += 1
            self.output_statistics['total_storage_used'] += len(docx_content)
            if pdf_content:
                self.output_statistics['total_storage_used'] += len(pdf_content)
            
            self._log(f"Saved resume files for {person_name}")
            return str(docx_path), str(pdf_path) if pdf_path else None
            
        except Exception as e:
            self._log(f"Failed to save resume: {str(e)}", "ERROR")
            self.output_statistics['total_files_failed'] += 1
            raise
    
    def save_extraction_data(self, cv_file: CVFile, extraction_result: Any,
                           output_dir: Optional[str] = None) -> str:
        """Save extraction data for debugging/analysis"""
        try:
            # Determine output directory
            if output_dir:
                save_dir = Path(output_dir)
            else:
                person_name = self._sanitize_name(cv_file.file_name.split('.')[0])
                date_str = datetime.now().strftime('%Y%m%d')
                save_dir = self._create_output_directory(person_name, date_str, "extractions")
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"extraction_{cv_file.file_name}_{timestamp}.json"
            file_path = save_dir / filename
            
            # Prepare extraction data
            extraction_data = {
                'original_file': {
                    'name': cv_file.file_name,
                    'path': cv_file.file_path,
                    'size': cv_file.file_size,
                    'format': cv_file.file_format.value if hasattr(cv_file.file_format, 'value') else str(cv_file.file_format)
                },
                'extraction_result': {
                    'success': extraction_result.success,
                    'text_length': len(extraction_result.text) if extraction_result.text else 0,
                    'method': extraction_result.method.value if extraction_result.method else None,
                    'page_count': extraction_result.page_count,
                    'extraction_time': extraction_result.extraction_time,
                    'error': extraction_result.error
                },
                'extracted_text': extraction_result.text,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(extraction_data, f, indent=2, ensure_ascii=False)
            
            # Create output record
            output_record = self._create_output_record(
                cv_file, str(file_path), FileType.JSON, OutputStatus.CREATED
            )
            self.output_files[output_record.id] = output_record
            
            self._log(f"Saved extraction data: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self._log(f"Failed to save extraction data: {str(e)}", "ERROR")
            raise
    
    def save_processing_log(self, cv_file: CVFile, log_data: Dict[str, Any],
                          output_dir: Optional[str] = None) -> str:
        """Save processing log for audit trail"""
        try:
            # Determine output directory
            if output_dir:
                save_dir = Path(output_dir)
            else:
                person_name = self._sanitize_name(cv_file.file_name.split('.')[0])
                date_str = datetime.now().strftime('%Y%m%d')
                save_dir = self._create_output_directory(person_name, date_str, "logs")
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"processing_log_{cv_file.file_name}_{timestamp}.json"
            file_path = save_dir / filename
            
            # Prepare log data
            log_entry = {
                'original_file': {
                    'name': cv_file.file_name,
                    'path': cv_file.file_path,
                    'size': cv_file.file_size,
                    'format': cv_file.file_format.value if hasattr(cv_file.file_format, 'value') else str(cv_file.file_format)
                },
                'processing_log': log_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save log file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
            # Create output record
            output_record = self._create_output_record(
                cv_file, str(file_path), FileType.LOG, OutputStatus.CREATED
            )
            self.output_files[output_record.id] = output_record
            
            self._log(f"Saved processing log: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self._log(f"Failed to save processing log: {str(e)}", "ERROR")
            raise
    
    def _create_output_directory(self, person_name: str, date_str: str, 
                                subdir: str = "resumes") -> Path:
        """Create organized output directory structure"""
        if self.output_config.organize_by_date and self.output_config.organize_by_person:
            # Organize by date/person
            output_dir = self.base_dir / date_str / person_name / subdir
        elif self.output_config.organize_by_person:
            # Organize by person only
            output_dir = self.base_dir / person_name / subdir
        elif self.output_config.organize_by_date:
            # Organize by date only
            output_dir = self.base_dir / date_str / subdir
        else:
            # Flat structure
            output_dir = self.base_dir / subdir
        
        # Create directory
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def _generate_filename(self, person_name: str, date_str: str, 
                          file_type: str, output_type: FileType) -> str:
        """Generate standardized filename"""
        pattern = self.output_config.file_naming_pattern
        
        filename = pattern.format(
            person_name=person_name,
            date=date_str,
            type=file_type,
            timestamp=datetime.now().strftime('%H%M%S')
        )
        
        # Add appropriate extension
        if output_type == FileType.DOCX:
            filename += ".docx"
        elif output_type == FileType.PDF:
            filename += ".pdf"
        elif output_type == FileType.JSON:
            filename += ".json"
        elif output_type == FileType.LOG:
            filename += ".log"
        
        return filename
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for filesystem compatibility"""
        # Remove/replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Remove extra spaces and limit length
        name = '_'.join(name.split())
        return name[:50]  # Limit to 50 characters
    
    def _save_metadata(self, output_dir: Path, cv_file: CVFile, 
                      cv_data: CVData, additional_metadata: Dict[str, Any] = None) -> str:
        """Save metadata file"""
        metadata = {
            'original_file': {
                'name': cv_file.file_name,
                'path': cv_file.file_path,
                'size': cv_file.file_size,
                'format': cv_file.file_format.value if hasattr(cv_file.file_format, 'value') else str(cv_file.file_format),
                'created_date': cv_file.added_date.isoformat() if cv_file.added_date else None,
                'modified_date': cv_file.processed_date.isoformat() if cv_file.processed_date else None
            },
            'cv_data': {
                'person_name': cv_data.person_name,
                'personal_info': {
                    'full_name': cv_data.personal_info.full_name if cv_data.personal_info else None,
                    'first_name': cv_data.personal_info.first_name if cv_data.personal_info else None,
                    'last_name': cv_data.personal_info.last_name if cv_data.personal_info else None,
                    'location': cv_data.personal_info.location if cv_data.personal_info else None,
                    'email': cv_data.personal_info.email if cv_data.personal_info else None,
                    'phone': cv_data.personal_info.phone if cv_data.personal_info else None
                },
                'work_experience_count': len(cv_data.work_experience),
                'education_count': len(cv_data.education),
                'language': cv_data.language.value if cv_data.language and hasattr(cv_data.language, 'value') else str(cv_data.language) if cv_data.language else None
            },
            'processing': {
                'created_at': datetime.now().isoformat(),
                'processing_version': '1.0.0',
                'additional_metadata': additional_metadata or {}
            }
        }
        
        # Save metadata file
        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return str(metadata_path)
    
    def _create_output_record(self, cv_file: CVFile, output_path: str, 
                             file_type: FileType, status: OutputStatus,
                             metadata: Dict[str, Any] = None) -> OutputFile:
        """Create output file record"""
        # Generate unique ID
        output_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{cv_file.file_name[:20]}"
        
        # Calculate file size and checksum
        file_size = 0
        checksum = ""
        try:
            file_path = Path(output_path)
            if file_path.exists():
                file_size = file_path.stat().st_size
                checksum = self._calculate_checksum(file_path)
        except Exception:
            pass
        
        return OutputFile(
            id=output_id,
            original_file=cv_file,
            output_path=output_path,
            file_type=file_type,
            status=status,
            file_size=file_size,
            checksum=checksum,
            metadata=metadata or {}
        )
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum"""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return "unknown"
    
    def _create_backup(self, output_file: OutputFile):
        """Create backup of output file"""
        try:
            # Create backup directory
            backup_dir = self.base_dir / "backups" / datetime.now().strftime('%Y%m%d')
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime('%H%M%S')
            backup_filename = f"backup_{timestamp}_{Path(output_file.output_path).name}"
            backup_path = backup_dir / backup_filename
            
            # Copy file
            shutil.copy2(output_file.output_path, backup_path)
            
            # Update output file record
            output_file.backup_path = str(backup_path)
            output_file.status = OutputStatus.BACKED_UP
            
            self.output_statistics['total_backups_created'] += 1
            self._log(f"Created backup: {backup_path}")
            
        except Exception as e:
            self._log(f"Failed to create backup: {str(e)}", "ERROR")
    
    def cleanup_old_files(self, days_old: int = None):
        """Clean up old files based on configuration"""
        if days_old is None:
            days_old = self.output_config.archive_after_days
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        for output_file in self.output_files.values():
            if output_file.created_at < cutoff_date:
                try:
                    # Archive file
                    if self.output_config.archive_old_files:
                        self._archive_file(output_file)
                    
                    # Remove from tracking
                    if output_file.id in self.output_files:
                        del self.output_files[output_file.id]
                    
                    cleaned_count += 1
                    
                except Exception as e:
                    self._log(f"Failed to clean up {output_file.id}: {str(e)}", "ERROR")
        
        self._log(f"Cleaned up {cleaned_count} old files")
    
    def _archive_file(self, output_file: OutputFile):
        """Archive old file"""
        try:
            # Create archive directory
            archive_dir = self.base_dir / "archives" / output_file.created_at.strftime('%Y%m')
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate archive filename
            archive_filename = f"archive_{output_file.id}_{Path(output_file.output_path).name}"
            archive_path = archive_dir / archive_filename
            
            # Move file to archive
            shutil.move(output_file.output_path, archive_path)
            
            # Update record
            output_file.archive_path = str(archive_path)
            output_file.status = OutputStatus.ARCHIVED
            
            self.output_statistics['total_archives_created'] += 1
            self._log(f"Archived file: {archive_path}")
            
        except Exception as e:
            self._log(f"Failed to archive {output_file.id}: {str(e)}", "ERROR")
    
    def get_output_statistics(self) -> Dict[str, Any]:
        """Get output management statistics"""
        return {
            'total_files_created': self.output_statistics['total_files_created'],
            'total_files_updated': self.output_statistics['total_files_updated'],
            'total_files_failed': self.output_statistics['total_files_failed'],
            'total_backups_created': self.output_statistics['total_backups_created'],
            'total_archives_created': self.output_statistics['total_archives_created'],
            'total_storage_used_bytes': self.output_statistics['total_storage_used'],
            'total_storage_used_mb': self.output_statistics['total_storage_used'] / (1024 * 1024),
            'active_output_files': len(self.output_files),
            'output_configuration': {
                'base_output_dir': self.output_config.base_output_dir,
                'organize_by_date': self.output_config.organize_by_date,
                'organize_by_person': self.output_config.organize_by_person,
                'create_backups': self.output_config.create_backups,
                'archive_old_files': self.output_config.archive_old_files
            }
        }
    
    def _ensure_directory_structure(self):
        """Ensure base directory structure exists"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_dir / "backups").mkdir(exist_ok=True)
        (self.base_dir / "archives").mkdir(exist_ok=True)
        (self.base_dir / "logs").mkdir(exist_ok=True)
        (self.base_dir / "extractions").mkdir(exist_ok=True)
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [OutputManager] {message}")
