#!/usr/bin/env python3
"""
Validation Engine - Comprehensive validation system
Generic validation engine with rule-based validation and quality scoring
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from src.core import CVData, ExtractionResult, CVFile


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    CRITICAL = "critical"    # Must fix
    WARNING = "warning"      # Should fix
    INFO = "info"           # Nice to have
    SUCCESS = "success"      # Validation passed


@dataclass
class ValidationResult:
    """Result of a validation check"""
    rule_name: str
    level: ValidationLevel
    message: str
    passed: bool
    score: float  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report"""
    overall_score: float  # 0.0 to 1.0
    passed_checks: int
    total_checks: int
    critical_issues: int
    warnings: int
    info_items: int
    results: List[ValidationResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    validation_time: datetime = field(default_factory=datetime.now)


class ValidationRule:
    """Base class for validation rules"""
    
    def __init__(self, name: str, description: str, level: ValidationLevel = ValidationLevel.WARNING):
        self.name = name
        self.description = description
        self.level = level
    
    def validate(self, data: Any) -> ValidationResult:
        """Validate data and return result"""
        raise NotImplementedError


class ValidationEngine:
    """
    Generic validation engine with comprehensive rule system
    
    Features:
    - Rule-based validation
    - Quality scoring
    - Custom validation rules
    - Batch validation
    - Validation reporting
    - Performance tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize validation engine"""
        self.config = config or {}
        self.rules: Dict[str, ValidationRule] = {}
        self.validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'average_score': 0.0
        }
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default validation rules"""
        # File validation rules
        self.add_rule(FileSizeRule())
        self.add_rule(FileFormatRule())
        self.add_rule(FileAccessRule())
        
        # Text extraction rules
        self.add_rule(TextLengthRule())
        self.add_rule(TextQualityRule())
        self.add_rule(CharacterEncodingRule())
        
        # CV data rules
        self.add_rule(PersonalInfoRule())
        self.add_rule(WorkExperienceRule())
        self.add_rule(EducationRule())
        self.add_rule(ContactInfoRule())
        
        # Quality rules
        self.add_rule(CompletenessRule())
        self.add_rule(ConsistencyRule())
        self.add_rule(FormattingRule())
    
    def add_rule(self, rule: ValidationRule):
        """Add custom validation rule"""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """Remove validation rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
    
    def validate_file(self, cv_file: CVFile) -> ValidationReport:
        """Validate CV file"""
        results = []
        
        # Run file-level validations
        for rule_name, rule in self.rules.items():
            if hasattr(rule, 'validate_file'):
                try:
                    result = rule.validate_file(cv_file)
                    results.append(result)
                except Exception as e:
                    results.append(ValidationResult(
                        rule_name=rule_name,
                        level=ValidationLevel.CRITICAL,
                        message=f"Validation error: {str(e)}",
                        passed=False,
                        score=0.0
                    ))
        
        return self._create_report(results)
    
    def validate_extraction(self, extraction_result: ExtractionResult) -> ValidationReport:
        """Validate text extraction result"""
        results = []
        
        # Run extraction-level validations
        for rule_name, rule in self.rules.items():
            if hasattr(rule, 'validate_extraction'):
                try:
                    result = rule.validate_extraction(extraction_result)
                    results.append(result)
                except Exception as e:
                    results.append(ValidationResult(
                        rule_name=rule_name,
                        level=ValidationLevel.CRITICAL,
                        message=f"Validation error: {str(e)}",
                        passed=False,
                        score=0.0
                    ))
        
        return self._create_report(results)
    
    def validate_cv_data(self, cv_data: CVData) -> ValidationReport:
        """Validate structured CV data"""
        results = []
        
        # Run CV data validations
        for rule_name, rule in self.rules.items():
            if hasattr(rule, 'validate_cv_data'):
                try:
                    result = rule.validate_cv_data(cv_data)
                    results.append(result)
                except Exception as e:
                    results.append(ValidationResult(
                        rule_name=rule_name,
                        level=ValidationLevel.CRITICAL,
                        message=f"Validation error: {str(e)}",
                        passed=False,
                        score=0.0
                    ))
        
        return self._create_report(results)
    
    def validate_complete_pipeline(self, cv_file: CVFile, extraction_result: ExtractionResult, cv_data: CVData) -> ValidationReport:
        """Validate complete processing pipeline"""
        results = []
        
        # Validate each stage
        file_report = self.validate_file(cv_file)
        extraction_report = self.validate_extraction(extraction_result)
        data_report = self.validate_cv_data(cv_data)
        
        # Combine all results
        results.extend(file_report.results)
        results.extend(extraction_report.results)
        results.extend(data_report.results)
        
        # Add pipeline-specific validations
        pipeline_result = self._validate_pipeline_consistency(cv_file, extraction_result, cv_data)
        results.append(pipeline_result)
        
        return self._create_report(results)
    
    def _validate_pipeline_consistency(self, cv_file: CVFile, extraction_result: ExtractionResult, cv_data: CVData) -> ValidationResult:
        """Validate consistency across pipeline stages"""
        issues = []
        score = 1.0
        
        # Check file name consistency
        if cv_file.file_name and cv_data.person_name:
            if cv_file.file_name.lower() not in cv_data.person_name.lower() and cv_data.person_name.lower() not in cv_file.file_name.lower():
                issues.append("File name doesn't match extracted person name")
                score -= 0.1
        
        # Check text extraction consistency
        if extraction_result.success and cv_data.raw_text:
            if len(extraction_result.text) != len(cv_data.raw_text):
                issues.append("Text length mismatch between extraction and CV data")
                score -= 0.2
        
        # Check data completeness
        if not cv_data.personal_info or not cv_data.personal_info.full_name:
            issues.append("Missing personal information")
            score -= 0.3
        
        passed = len(issues) == 0
        return ValidationResult(
            rule_name="Pipeline Consistency",
            level=ValidationLevel.WARNING if issues else ValidationLevel.SUCCESS,
            message="Pipeline consistency check",
            passed=passed,
            score=max(0.0, score),
            details={'issues': issues}
        )
    
    def _create_report(self, results: List[ValidationResult]) -> ValidationReport:
        """Create validation report from results"""
        if not results:
            return ValidationReport(
                overall_score=1.0,
                passed_checks=0,
                total_checks=0,
                critical_issues=0,
                warnings=0,
                info_items=0
            )
        
        # Calculate statistics
        passed_checks = sum(1 for r in results if r.passed)
        total_checks = len(results)
        critical_issues = sum(1 for r in results if r.level == ValidationLevel.CRITICAL and not r.passed)
        warnings = sum(1 for r in results if r.level == ValidationLevel.WARNING and not r.passed)
        info_items = sum(1 for r in results if r.level == ValidationLevel.INFO)
        
        # Calculate overall score
        overall_score = sum(r.score for r in results) / len(results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results)
        
        # Update stats
        self.validation_stats['total_validations'] += 1
        if overall_score >= 0.8:
            self.validation_stats['passed_validations'] += 1
        else:
            self.validation_stats['failed_validations'] += 1
        
        self.validation_stats['average_score'] = (
            (self.validation_stats['average_score'] * (self.validation_stats['total_validations'] - 1) + overall_score) 
            / self.validation_stats['total_validations']
        )
        
        return ValidationReport(
            overall_score=overall_score,
            passed_checks=passed_checks,
            total_checks=total_checks,
            critical_issues=critical_issues,
            warnings=warnings,
            info_items=info_items,
            results=results,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Critical issues
        critical_failures = [r for r in results if r.level == ValidationLevel.CRITICAL and not r.passed]
        if critical_failures:
            recommendations.append(f"Fix {len(critical_failures)} critical issues before processing")
        
        # Common issues
        common_issues = {}
        for result in results:
            if not result.passed and result.level != ValidationLevel.INFO:
                rule_name = result.rule_name
                common_issues[rule_name] = common_issues.get(rule_name, 0) + 1
        
        if common_issues:
            most_common = max(common_issues.items(), key=lambda x: x[1])
            recommendations.append(f"Most common issue: {most_common[0]} ({most_common[1]} occurrences)")
        
        # Quality improvements
        low_scores = [r for r in results if r.score < 0.5]
        if low_scores:
            recommendations.append(f"Improve quality in {len(low_scores)} areas for better results")
        
        return recommendations
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation engine statistics"""
        return {
            'total_validations': self.validation_stats['total_validations'],
            'passed_validations': self.validation_stats['passed_validations'],
            'failed_validations': self.validation_stats['failed_validations'],
            'success_rate': (
                self.validation_stats['passed_validations'] / self.validation_stats['total_validations'] 
                if self.validation_stats['total_validations'] > 0 else 0
            ),
            'average_score': self.validation_stats['average_score'],
            'active_rules': len(self.rules),
            'rule_names': list(self.rules.keys())
        }


# Default Validation Rules

class FileSizeRule(ValidationRule):
    """Validate file size"""
    
    def __init__(self):
        super().__init__("File Size", "Validate file size is within acceptable range")
    
    def validate_file(self, cv_file: CVFile) -> ValidationResult:
        min_size = 1024  # 1KB
        max_size = 50 * 1024 * 1024  # 50MB
        
        if cv_file.file_size < min_size:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message=f"File too small ({cv_file.file_size} bytes)",
                passed=False,
                score=0.0,
                suggestions=["Check if file is corrupted or incomplete"]
            )
        elif cv_file.file_size > max_size:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message=f"File too large ({cv_file.file_size} bytes)",
                passed=False,
                score=0.0,
                suggestions=["Consider compressing or splitting the file"]
            )
        else:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.SUCCESS,
                message=f"File size acceptable ({cv_file.file_size} bytes)",
                passed=True,
                score=1.0
            )


class TextLengthRule(ValidationRule):
    """Validate extracted text length"""
    
    def __init__(self):
        super().__init__("Text Length", "Validate extracted text has sufficient length")
    
    def validate_extraction(self, extraction_result: ExtractionResult) -> ValidationResult:
        min_length = 100
        optimal_length = 1000
        
        if not extraction_result.success:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.CRITICAL,
                message="Text extraction failed",
                passed=False,
                score=0.0
            )
        
        text_length = len(extraction_result.text)
        
        if text_length < min_length:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.CRITICAL,
                message=f"Text too short ({text_length} characters)",
                passed=False,
                score=0.0,
                suggestions=["Try OCR extraction or check if file is image-based"]
            )
        elif text_length < optimal_length:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message=f"Text length below optimal ({text_length} characters)",
                passed=True,
                score=0.7,
                suggestions=["Consider manual review for completeness"]
            )
        else:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.SUCCESS,
                message=f"Text length good ({text_length} characters)",
                passed=True,
                score=1.0
            )


class PersonalInfoRule(ValidationRule):
    """Validate personal information completeness"""
    
    def __init__(self):
        super().__init__("Personal Info", "Validate personal information is complete")
    
    def validate_cv_data(self, cv_data: CVData) -> ValidationResult:
        issues = []
        score = 1.0
        
        if not cv_data.personal_info:
            issues.append("No personal information found")
            score = 0.0
        else:
            pi = cv_data.personal_info
            
            if not pi.full_name or len(pi.full_name.strip()) < 2:
                issues.append("Missing or invalid full name")
                score -= 0.3
            
            if not pi.first_name or len(pi.first_name.strip()) < 1:
                issues.append("Missing first name")
                score -= 0.2
            
            if not pi.last_name or len(pi.last_name.strip()) < 1:
                issues.append("Missing last name")
                score -= 0.2
            
            if not pi.location or len(pi.location.strip()) < 2:
                issues.append("Missing location information")
                score -= 0.1
        
        passed = len(issues) == 0
        level = ValidationLevel.CRITICAL if score < 0.5 else ValidationLevel.WARNING if issues else ValidationLevel.SUCCESS
        
        return ValidationResult(
            rule_name=self.name,
            level=level,
            message=f"Personal information validation ({len(issues)} issues)",
            passed=passed,
            score=max(0.0, score),
            details={'issues': issues},
            suggestions=self._get_personal_info_suggestions(issues)
        )
    
    def _get_personal_info_suggestions(self, issues: List[str]) -> List[str]:
        """Get suggestions for personal info issues"""
        suggestions = []
        
        if "No personal information found" in issues:
            suggestions.append("Check if CV contains personal details section")
        
        if "Missing or invalid full name" in issues:
            suggestions.append("Look for name in CV header or contact section")
        
        if "Missing location information" in issues:
            suggestions.append("Extract address, city, or country information")
        
        return suggestions


# Additional rule classes would be implemented here...
class FileFormatRule(ValidationRule):
    def __init__(self):
        super().__init__("File Format", "Validate file format is supported")
    
    def validate_file(self, cv_file: CVFile) -> ValidationResult:
        if cv_file.file_format.value == ".unknown":
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.CRITICAL,
                message="Unsupported file format",
                passed=False,
                score=0.0
            )
        return ValidationResult(
            rule_name=self.name,
            level=ValidationLevel.SUCCESS,
            message=f"Supported format: {cv_file.file_format.value}",
            passed=True,
            score=1.0
        )


class FileAccessRule(ValidationRule):
    def __init__(self):
        super().__init__("File Access", "Validate file can be accessed")
    
    def validate_file(self, cv_file: CVFile) -> ValidationResult:
        try:
            with open(cv_file.file_path, 'rb') as f:
                f.read(1)
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.SUCCESS,
                message="File accessible",
                passed=True,
                score=1.0
            )
        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.CRITICAL,
                message=f"Cannot access file: {str(e)}",
                passed=False,
                score=0.0
            )


class TextQualityRule(ValidationRule):
    def __init__(self):
        super().__init__("Text Quality", "Validate text quality and readability")
    
    def validate_extraction(self, extraction_result: ExtractionResult) -> ValidationResult:
        if not extraction_result.success:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.CRITICAL,
                message="No text to validate",
                passed=False,
                score=0.0
            )
        
        text = extraction_result.text
        printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
        quality_ratio = printable_chars / len(text) if text else 0
        
        if quality_ratio < 0.8:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message=f"Low text quality ({quality_ratio:.2f})",
                passed=False,
                score=quality_ratio,
                suggestions=["Text may contain encoding issues or OCR artifacts"]
            )
        
        return ValidationResult(
            rule_name=self.name,
            level=ValidationLevel.SUCCESS,
            message=f"Good text quality ({quality_ratio:.2f})",
            passed=True,
            score=quality_ratio
        )


class CharacterEncodingRule(ValidationRule):
    def __init__(self):
        super().__init__("Character Encoding", "Validate character encoding")
    
    def validate_extraction(self, extraction_result: ExtractionResult) -> ValidationResult:
        if not extraction_result.success:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.CRITICAL,
                message="No text to validate",
                passed=False,
                score=0.0
            )
        
        try:
            # Try to encode/decode to check for encoding issues
            text = extraction_result.text
            text.encode('utf-8').decode('utf-8')
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.SUCCESS,
                message="Valid UTF-8 encoding",
                passed=True,
                score=1.0
            )
        except UnicodeError:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message="Character encoding issues detected",
                passed=False,
                score=0.5,
                suggestions=["Check file encoding or try different extraction method"]
            )


class WorkExperienceRule(ValidationRule):
    def __init__(self):
        super().__init__("Work Experience", "Validate work experience data")
    
    def validate_cv_data(self, cv_data: CVData) -> ValidationResult:
        if not cv_data.work_experience:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message="No work experience found",
                passed=True,
                score=0.5,
                suggestions=["Check if CV contains work history section"]
            )
        
        valid_experiences = 0
        for exp in cv_data.work_experience:
            if exp.company and exp.position:
                valid_experiences += 1
        
        if valid_experiences == 0:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message="No valid work experiences found",
                passed=False,
                score=0.2
            )
        
        score = valid_experiences / len(cv_data.work_experience)
        return ValidationResult(
            rule_name=self.name,
            level=ValidationLevel.SUCCESS,
            message=f"Found {valid_experiences} valid work experiences",
            passed=True,
            score=score
        )


class EducationRule(ValidationRule):
    def __init__(self):
        super().__init__("Education", "Validate education data")
    
    def validate_cv_data(self, cv_data: CVData) -> ValidationResult:
        if not cv_data.education:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.INFO,
                message="No education information found",
                passed=True,
                score=0.5
            )
        
        valid_education = 0
        for edu in cv_data.education:
            if edu.institution and edu.degree:
                valid_education += 1
        
        score = valid_education / len(cv_data.education) if cv_data.education else 0
        return ValidationResult(
            rule_name=self.name,
            level=ValidationLevel.SUCCESS,
            message=f"Found {valid_education} valid education entries",
            passed=True,
            score=score
        )


class ContactInfoRule(ValidationRule):
    def __init__(self):
        super().__init__("Contact Info", "Validate contact information")
    
    def validate_cv_data(self, cv_data: CVData) -> ValidationResult:
        if not cv_data.personal_info:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message="No personal info to validate contact details",
                passed=False,
                score=0.0
            )
        
        pi = cv_data.personal_info
        contact_score = 0.0
        
        if pi.email:
            contact_score += 0.4
        if pi.phone:
            contact_score += 0.3
        if pi.location:
            contact_score += 0.3
        
        if contact_score == 0:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.WARNING,
                message="No contact information found",
                passed=False,
                score=0.0,
                suggestions=["Extract email, phone, or address from CV"]
            )
        
        return ValidationResult(
            rule_name=self.name,
            level=ValidationLevel.SUCCESS,
            message=f"Contact information completeness: {contact_score:.1f}",
            passed=True,
            score=contact_score
        )


class CompletenessRule(ValidationRule):
    def __init__(self):
        super().__init__("Completeness", "Validate overall CV completeness")
    
    def validate_cv_data(self, cv_data: CVData) -> ValidationResult:
        completeness_score = 0.0
        
        # Personal info (30%)
        if cv_data.personal_info and cv_data.personal_info.full_name:
            completeness_score += 0.3
        
        # Work experience (40%)
        if cv_data.work_experience and len(cv_data.work_experience) > 0:
            completeness_score += 0.4
        
        # Education (20%)
        if cv_data.education and len(cv_data.education) > 0:
            completeness_score += 0.2
        
        # Contact info (10%)
        if cv_data.personal_info and (cv_data.personal_info.email or cv_data.personal_info.phone):
            completeness_score += 0.1
        
        if completeness_score < 0.5:
            level = ValidationLevel.WARNING
        elif completeness_score < 0.8:
            level = ValidationLevel.INFO
        else:
            level = ValidationLevel.SUCCESS
        
        return ValidationResult(
            rule_name=self.name,
            level=level,
            message=f"CV completeness: {completeness_score:.1f}",
            passed=completeness_score >= 0.5,
            score=completeness_score
        )


class ConsistencyRule(ValidationRule):
    def __init__(self):
        super().__init__("Consistency", "Validate data consistency")
    
    def validate_cv_data(self, cv_data: CVData) -> ValidationResult:
        issues = []
        score = 1.0
        
        # Check date consistency
        if cv_data.work_experience:
            for exp in cv_data.work_experience:
                if exp.start_date and exp.end_date:
                    if exp.start_date > exp.end_date:
                        issues.append(f"Invalid date range for {exp.company}")
                        score -= 0.1
        
        # Check name consistency
        if cv_data.personal_info:
            pi = cv_data.personal_info
            if pi.first_name and pi.last_name and pi.full_name:
                expected_full = f"{pi.first_name} {pi.last_name}"
                if expected_full.lower() not in pi.full_name.lower():
                    issues.append("Name components don't match full name")
                    score -= 0.1
        
        passed = len(issues) == 0
        return ValidationResult(
            rule_name=self.name,
            level=ValidationLevel.WARNING if issues else ValidationLevel.SUCCESS,
            message=f"Consistency check ({len(issues)} issues)",
            passed=passed,
            score=max(0.0, score),
            details={'issues': issues}
        )


class FormattingRule(ValidationRule):
    def __init__(self):
        super().__init__("Formatting", "Validate text formatting quality")
    
    def validate_extraction(self, extraction_result: ExtractionResult) -> ValidationResult:
        if not extraction_result.success:
            return ValidationResult(
                rule_name=self.name,
                level=ValidationLevel.CRITICAL,
                message="No text to validate",
                passed=False,
                score=0.0
            )
        
        text = extraction_result.text
        issues = []
        score = 1.0
        
        # Check for excessive whitespace
        if '  ' in text:  # Double spaces
            issues.append("Excessive whitespace detected")
            score -= 0.1
        
        # Check for mixed line endings
        if '\r\n' in text and '\n' in text:
            issues.append("Mixed line endings detected")
            score -= 0.1
        
        # Check for encoding artifacts
        if '�' in text:
            issues.append("Encoding artifacts detected")
            score -= 0.2
        
        passed = len(issues) == 0
        return ValidationResult(
            rule_name=self.name,
            level=ValidationLevel.INFO if issues else ValidationLevel.SUCCESS,
            message=f"Formatting check ({len(issues)} issues)",
            passed=passed,
            score=max(0.0, score),
            details={'issues': issues}
        )
