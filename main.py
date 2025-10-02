#!/usr/bin/env python3
"""
CV Automation - Main Orchestrator
=================================

This is the main entry point for the CV automation system.
It orchestrates all layers to convert CVs into Synergie Resumés.

Architecture:
- Input Layer: File discovery and validation
- Extraction Layer: Text extraction from various formats
- Parsing Layer: Structured data parsing
- Generation Layer: Synergie Resumé creation
- Quality Layer: Data validation and quality checks
- Output Layer: File management and delivery
- Monitoring Layer: Progress tracking and reporting

Usage:
    python main.py --input "path/to/cvs" --output "path/to/resumes"
    python main.py --single "path/to/cv.pdf" --output "path/to/output"
    python main.py --batch --input "Netwerk Folder" --output "Generated Resumés"
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core import (
    CVFile, PersonalInfo, WorkExperience, CVData, ProcessingStatus,
    FileFormat, Language, ProcessingConfig, LogConfig, Paths,
    CVAutomationException, ValidationException, GenerationException
)
from src.extraction import ExtractorFactory, ExtractionResult
from src.extraction.parsers import CVParser
from src.generation import ResumeGenerator


class CVAutomationOrchestrator:
    """
    Main orchestrator for CV automation system.
    
    This class coordinates all layers to process CVs into Synergie Resumés:
    1. Input: Discover and validate CV files
    2. Extraction: Extract text from various formats
    3. Parsing: Parse into structured data
    4. Generation: Create Synergie Resumés
    5. Quality: Validate output quality
    6. Output: Manage file delivery
    7. Monitoring: Track progress and report
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None, log_level: str = "INFO"):
        """Initialize the orchestrator with configuration."""
        self.config = config or ProcessingConfig()
        self.log_level = log_level
        self.setup_logging()
        
        # Initialize components
        self.extractor_factory = ExtractorFactory()
        self.parser = CVParser()
        self.generator = ResumeGenerator()
        
        # Statistics tracking
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'successful_extractions': 0,
            'successful_parsings': 0,
            'successful_generations': 0,
            'failed_files': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Error tracking
        self.errors = []
        
        self.logger.info("CV Automation Orchestrator initialized")
    
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.log_level.upper())
        
        # Create logs directory if it doesn't exist
        os.makedirs(Paths.LOGS_DIR, exist_ok=True)
        
        # Setup file logging
        log_file = os.path.join(Paths.LOGS_DIR, f"cv_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=log_level,
            format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging initialized - Level: {self.log_level}")
    
    def discover_cv_files(self, input_path: str) -> List[CVFile]:
        """
        Discover CV files in the input directory.
        
        Args:
            input_path: Path to directory containing CVs
            
        Returns:
            List of discovered CV files
            
        Raises:
            CVAutomationException: If input path is invalid or no files found
        """
        self.logger.info(f"Discovering CV files in: {input_path}")
        
        if not os.path.exists(input_path):
            raise CVAutomationException(f"Input path does not exist: {input_path}")
        
        if not os.path.isdir(input_path):
            raise CVAutomationException(f"Input path is not a directory: {input_path}")
        
        cv_files = []
        supported_extensions = {'.pdf', '.docx', '.doc'}
        
        # Walk through directory tree
        for root, dirs, files in os.walk(input_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                # Skip if not supported format
                if file_ext not in supported_extensions:
                    continue
                
                # Skip if already processed (Synergie Resumé)
                if file.startswith('Resumé_Synergie'):
                    self.logger.debug(f"Skipping processed Resumé: {file}")
                    continue
                
                try:
                    # Create CV file object
                    cv_file = CVFile(
                        id=self._generate_file_id(file_path),
                        person_name=self._extract_person_name(file),
                        file_path=file_path,
                        file_name=file,
                        file_format=FileFormat.from_extension(file_ext),
                        file_size=os.path.getsize(file_path),
                        status=ProcessingStatus.PENDING
                    )
                    
                    cv_files.append(cv_file)
                    self.logger.debug(f"Discovered CV: {file}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process file {file}: {e}")
                    continue
        
        if not cv_files:
            raise CVAutomationException(f"No CV files found in: {input_path}")
        
        self.stats['total_files'] = len(cv_files)
        self.logger.info(f"Discovered {len(cv_files)} CV files")
        
        return cv_files
    
    def process_single_cv(self, cv_file: CVFile, output_dir: str) -> Dict[str, Any]:
        """
        Process a single CV file through the complete pipeline.
        
        Args:
            cv_file: CV file to process
            output_dir: Directory to save generated Resumé
            
        Returns:
            Dictionary with processing results
        """
        self.logger.info(f"Processing CV: {cv_file.file_name}")
        
        result = {
            'file_id': cv_file.id,
            'file_name': cv_file.file_name,
            'person_name': cv_file.person_name,
            'status': 'failed',
            'steps_completed': [],
            'errors': [],
            'output_file': None,
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Step 1: Extraction
            self.logger.info(f"Step 1: Extracting text from {cv_file.file_name}")
            extraction_result = self._extract_text(cv_file)
            
            if not extraction_result.success:
                raise CVAutomationException(f"Extraction failed: {extraction_result.error}")
            
            result['steps_completed'].append('extraction')
            self.stats['successful_extractions'] += 1
            
            # Step 2: Parsing
            self.logger.info(f"Step 2: Parsing structured data from {cv_file.file_name}")
            parsing_result = self._parse_cv_data(extraction_result.text, cv_file)
            
            if not parsing_result['success']:
                raise CVAutomationException(f"Parsing failed: {parsing_result['error_message']}")
            
            result['steps_completed'].append('parsing')
            self.stats['successful_parsings'] += 1
            
            # Step 3: Generation
            self.logger.info(f"Step 3: Generating Synergie Resumé for {cv_file.file_name}")
            
            # Extract the actual CV data from the parsing result
            cv_data_object = parsing_result['cv_data']
            generation_result = self._generate_resume(cv_data_object, output_dir)
            
            if not generation_result['success']:
                raise CVAutomationException(f"Generation failed: {generation_result['error_message']}")
            
            result['steps_completed'].append('generation')
            result['output_file'] = generation_result['output_file']
            self.stats['successful_generations'] += 1
            
            # Step 4: Quality Check
            self.logger.info(f"Step 4: Quality check for {cv_file.file_name}")
            quality_result = self._quality_check(generation_result['output_file'], parsing_result['cv_data'])
            
            if quality_result['passed']:
                result['steps_completed'].append('quality_check')
                result['status'] = 'success'
            else:
                result['warnings'] = quality_result['warnings']
                result['status'] = 'success_with_warnings'
            
            self.stats['processed_files'] += 1
            
        except Exception as e:
            error_msg = f"Processing failed for {cv_file.file_name}: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            self.errors.append({
                'file': cv_file.file_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self.stats['failed_files'] += 1
        
        finally:
            end_time = datetime.now()
            result['processing_time'] = (end_time - start_time).total_seconds()
            cv_file.status = ProcessingStatus.COMPLETED if result['status'] == 'success' else ProcessingStatus.FAILED
        
        return result
    
    def process_batch(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Process all CVs in a directory.
        
        Args:
            input_path: Directory containing CVs
            output_dir: Directory to save generated Resumés
            
        Returns:
            Batch processing results
        """
        self.logger.info(f"Starting batch processing: {input_path} -> {output_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Discover CV files
        cv_files = self.discover_cv_files(input_path)
        
        # Initialize batch results
        batch_result = {
            'input_path': input_path,
            'output_dir': output_dir,
            'total_files': len(cv_files),
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'results': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        self.stats['start_time'] = datetime.now()
        
        # Process each CV
        for i, cv_file in enumerate(cv_files, 1):
            self.logger.info(f"Processing file {i}/{len(cv_files)}: {cv_file.file_name}")
            
            try:
                result = self.process_single_cv(cv_file, output_dir)
                batch_result['results'].append(result)
                batch_result['processed_files'] += 1
                
                if result['status'] in ['success', 'success_with_warnings']:
                    batch_result['successful_files'] += 1
                else:
                    batch_result['failed_files'] += 1
                
                # Progress update
                progress = (i / len(cv_files)) * 100
                self.logger.info(f"Progress: {progress:.1f}% ({i}/{len(cv_files)})")
                
            except Exception as e:
                error_msg = f"Failed to process {cv_file.file_name}: {str(e)}"
                self.logger.error(error_msg)
                batch_result['failed_files'] += 1
                self.stats['failed_files'] += 1
        
        batch_result['end_time'] = datetime.now().isoformat()
        self.stats['end_time'] = datetime.now()
        
        # Generate summary
        self._generate_batch_summary(batch_result)
        
        return batch_result
    
    def _extract_text(self, cv_file: CVFile) -> ExtractionResult:
        """Extract text from CV file."""
        try:
            return self.extractor_factory.extract(cv_file)
        except Exception as e:
            return ExtractionResult(
                success=False,
                text="",
                error=f"Extraction failed: {str(e)}",
                method=None
            )
    
    def _parse_cv_data(self, text: str, cv_file: CVFile) -> Dict[str, Any]:
        """Parse CV text into structured data."""
        try:
            # Create extraction result
            extraction_result = ExtractionResult(
                success=True,
                text=text,
                method=None,
                char_count=len(text)
            )
            
            # Parse using CVParser with filename
            result = self.parser.parse_cv(extraction_result, cv_file.file_name)
            
            if result['success']:
                return {
                    'success': True,
                    'cv_data': result,
                    'error_message': None,
                    'confidence': result.get('confidence', 0.0)
                }
            else:
                return {
                    'success': False,
                    'cv_data': None,
                    'error_message': result.get('error', 'Parsing failed'),
                    'confidence': 0.0
                }
                
        except Exception as e:
            return {
                'success': False,
                'cv_data': None,
                'error_message': f"Parsing failed: {str(e)}",
                'confidence': 0.0
            }
    
    def _generate_resume(self, cv_data_object, output_dir: str) -> Dict[str, Any]:
        """Generate Synergie Resumé from CV data."""
        try:
            # Debug: Check the type of cv_data_object
            self.logger.debug(f"cv_data_object type: {type(cv_data_object)}")
            self.logger.debug(f"cv_data_object: {cv_data_object}")
            
            # Handle both CVData object and dictionary
            if hasattr(cv_data_object, 'personal_info'):
                # It's a CVData object
                personal_info = cv_data_object.personal_info
                work_experience = cv_data_object.work_experience
                education = cv_data_object.education
                skills = cv_data_object.skills
                profile = cv_data_object.profile
            elif 'cv_data' in cv_data_object:
                # It's a parsing result dictionary with nested CVData
                cv_data = cv_data_object['cv_data']
                personal_info = cv_data.personal_info
                work_experience = cv_data.work_experience
                education = cv_data.education
                skills = cv_data.skills
                profile = cv_data.profile
            else:
                # It's a dictionary (fallback)
                personal_info = cv_data_object.get('personal_info', {})
                work_experience = cv_data_object.get('work_experience', [])
                education = cv_data_object.get('education', [])
                skills = cv_data_object.get('skills', [])
                profile = cv_data_object.get('profile')
            
            # Generate output filename
            person_name = personal_info.full_name if hasattr(personal_info, 'full_name') else personal_info.get('full_name', 'Unknown')
            safe_name = person_name.replace(" ", "_").replace("/", "_")
            output_filename = f"Resumé_Synergie_{safe_name}.docx"
            output_path = os.path.join(output_dir, output_filename)
            
            # Convert CVData object to dictionary for the generator
            cv_data_dict = {
                'personal_info': {
                    'full_name': personal_info.full_name if hasattr(personal_info, 'full_name') else personal_info.get('full_name'),
                    'first_name': personal_info.first_name if hasattr(personal_info, 'first_name') else personal_info.get('first_name'),
                    'last_name': personal_info.last_name if hasattr(personal_info, 'last_name') else personal_info.get('last_name'),
                    'location': personal_info.location if hasattr(personal_info, 'location') else personal_info.get('location'),
                    'phone': personal_info.phone if hasattr(personal_info, 'phone') else personal_info.get('phone'),
                    'email': personal_info.email if hasattr(personal_info, 'email') else personal_info.get('email')
                },
                'work_experience': [
                    {
                        'company': exp.company if hasattr(exp, 'company') else exp.get('company'),
                        'position': exp.position if hasattr(exp, 'position') else exp.get('position'),
                        'description': (exp.description or '') if hasattr(exp, 'description') else exp.get('description', ''),
                        'start_date': exp.start_date if hasattr(exp, 'start_date') else exp.get('start_date'),
                        'end_date': exp.end_date if hasattr(exp, 'end_date') else exp.get('end_date'),
                        'is_current': exp.is_current if hasattr(exp, 'is_current') else exp.get('is_current', False)
                    }
                    for exp in work_experience
                ],
                'education': [
                    {
                        'degree': edu.degree if hasattr(edu, 'degree') else edu.get('degree'),
                        'institution': edu.institution if hasattr(edu, 'institution') else edu.get('institution'),
                        'graduation_year': edu.graduation_year if hasattr(edu, 'graduation_year') else edu.get('graduation_year')
                    }
                    for edu in education
                ],
                'skills': skills,
                'profile': profile
            }
            
            # Generate resume
            generator = ResumeGenerator()
            result = generator.generate_resume(cv_data_dict, output_path, convert_to_pdf=False)
            
            if result['success']:
                return {
                    'success': True,
                    'output_file': result['docx_path'],
                    'error_message': None,
                    'processing_time': 0.0
                }
            else:
                return {
                    'success': False,
                    'output_file': None,
                    'error_message': result['error'],
                    'processing_time': 0.0
                }
                
        except Exception as e:
            return {
                'success': False,
                'output_file': None,
                'error_message': f"Generation failed: {str(e)}",
                'processing_time': 0.0
            }
    
    def _quality_check(self, output_file: str, cv_data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Perform quality check on generated Resumé."""
        quality_result = {
            'passed': True,
            'warnings': [],
            'score': 100
        }
        
        try:
            # Check if file exists and has reasonable size
            if not os.path.exists(output_file):
                quality_result['passed'] = False
                quality_result['warnings'].append("Output file does not exist")
                quality_result['score'] = 0
                return quality_result
            
            file_size = os.path.getsize(output_file)
            if file_size < 1000:  # Less than 1KB
                quality_result['warnings'].append("Output file is suspiciously small")
                quality_result['score'] -= 20
            
            # Check if personal info is present
            personal_info = cv_data_dict.get('personal_info')
            if not personal_info or not personal_info.get('full_name'):
                quality_result['warnings'].append("No personal information found")
                quality_result['score'] -= 30
            
            # Check if work experience is present
            work_experience = cv_data_dict.get('work_experience', [])
            if not work_experience:
                quality_result['warnings'].append("No work experience found")
                quality_result['score'] -= 20
            
            # Adjust passed status based on score
            if quality_result['score'] < 50:
                quality_result['passed'] = False
            
        except Exception as e:
            quality_result['passed'] = False
            quality_result['warnings'].append(f"Quality check failed: {str(e)}")
            quality_result['score'] = 0
        
        return quality_result
    
    def _generate_batch_summary(self, batch_result: Dict[str, Any]) -> None:
        """Generate and save batch processing summary."""
        summary = {
            'batch_summary': {
                'total_files': batch_result['total_files'],
                'successful_files': batch_result['successful_files'],
                'failed_files': batch_result['failed_files'],
                'success_rate': (batch_result['successful_files'] / batch_result['total_files'] * 100) if batch_result['total_files'] > 0 else 0,
                'processing_time': batch_result['end_time'],
                'start_time': batch_result['start_time']
            },
            'statistics': self.stats,
            'errors': self.errors
        }
        
        # Save summary to file
        summary_file = os.path.join(batch_result['output_dir'], f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Batch summary saved to: {summary_file}")
    
    def _generate_file_id(self, file_path: str) -> str:
        """Generate unique file ID."""
        import hashlib
        return hashlib.md5(file_path.encode()).hexdigest()[:12]
    
    def _extract_person_name(self, filename: str) -> str:
        """Extract person name from filename."""
        # Remove extension
        name = Path(filename).stem
        
        # Remove common prefixes
        prefixes = ['CV', 'cv', 'Resume', 'resume', 'Resumé', 'resumé']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                break
        
        # Clean up name
        name = name.replace('_', ' ').replace('-', ' ').strip()
        
        return name if name else "Unknown"


def main():
    """Main entry point for the CV automation system."""
    parser = argparse.ArgumentParser(
        description="CV Automation - Convert CVs to Synergie Resumés",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --single "CV John Doe.pdf" --output "output/"
  python main.py --batch --input "Netwerk Folder" --output "Generated Resumés"
  python main.py --input "cvs/" --output "resumes/" --config "config.json"
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--single', help='Process a single CV file')
    input_group.add_argument('--batch', action='store_true', help='Process all CVs in input directory')
    input_group.add_argument('--input', help='Input directory for batch processing')
    
    # Output options
    parser.add_argument('--output', required=True, help='Output directory for generated Resumés')
    
    # Configuration options
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    # Processing options
    parser.add_argument('--max-files', type=int, help='Maximum number of files to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        config = ProcessingConfig()
        orchestrator = CVAutomationOrchestrator(config, log_level=args.log_level)
        
        if args.single:
            # Single file processing
            if not os.path.exists(args.single):
                print(f"Error: File does not exist: {args.single}")
                sys.exit(1)
            
            cv_file = CVFile(
                id=orchestrator._generate_file_id(args.single),
                person_name=orchestrator._extract_person_name(os.path.basename(args.single)),
                file_path=args.single,
                file_name=os.path.basename(args.single),
                file_format=FileFormat.from_extension(Path(args.single).suffix.lower()),
                file_size=os.path.getsize(args.single)
            )
            
            result = orchestrator.process_single_cv(cv_file, args.output)
            
            if result['status'] == 'success':
                print(f"✅ Successfully processed: {result['file_name']}")
                print(f"📄 Output: {result['output_file']}")
            else:
                print(f"❌ Failed to process: {result['file_name']}")
                print(f"Errors: {result['errors']}")
                sys.exit(1)
        
        elif args.batch or args.input:
            # Batch processing
            input_path = args.input or "Netwerk Folder"
            
            if args.dry_run:
                cv_files = orchestrator.discover_cv_files(input_path)
                print(f"Would process {len(cv_files)} files:")
                for cv_file in cv_files:
                    print(f"  - {cv_file.file_name}")
                return
            
            batch_result = orchestrator.process_batch(input_path, args.output)
            
            print(f"\n📊 Batch Processing Complete!")
            print(f"Total files: {batch_result['total_files']}")
            print(f"Successful: {batch_result['successful_files']}")
            print(f"Failed: {batch_result['failed_files']}")
            print(f"Success rate: {(batch_result['successful_files'] / batch_result['total_files'] * 100):.1f}%")
            
            if batch_result['failed_files'] > 0:
                print(f"\n❌ Failed files:")
                for result in batch_result['results']:
                    if result['status'] == 'failed':
                        print(f"  - {result['file_name']}: {result['errors']}")
    
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
