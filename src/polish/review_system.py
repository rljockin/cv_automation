#!/usr/bin/env python3
"""
Review System - Quality control and manual review
Generic review system with automated quality checks and manual review workflows
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.core import CVData, ExtractionResult, CVFile
from .validation_engine import ValidationReport, ValidationLevel


class ReviewStatus(str, Enum):
    """Review status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ESCALATED = "escalated"


class ReviewType(str, Enum):
    """Type of review"""
    AUTOMATED = "automated"
    MANUAL = "manual"
    PEER = "peer"
    MANAGER = "manager"
    QUALITY_ASSURANCE = "quality_assurance"


@dataclass
class ReviewCriteria:
    """Review criteria and thresholds"""
    min_quality_score: float = 0.8
    max_processing_time: float = 300.0  # 5 minutes
    require_manual_review: bool = False
    auto_approve_threshold: float = 0.95
    escalation_threshold: float = 0.3
    review_timeout_hours: int = 24


@dataclass
class ReviewItem:
    """Item under review"""
    id: str
    cv_file: CVFile
    extraction_result: ExtractionResult
    cv_data: CVData
    validation_report: ValidationReport
    review_status: ReviewStatus = ReviewStatus.PENDING
    review_type: ReviewType = ReviewType.AUTOMATED
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewDecision:
    """Review decision and feedback"""
    review_item_id: str
    decision: ReviewStatus
    reviewer: str
    notes: List[str]
    quality_score: float
    feedback: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ReviewSystem:
    """
    Generic review system with automated and manual review capabilities
    
    Features:
    - Automated quality assessment
    - Manual review workflows
    - Review assignment and tracking
    - Quality metrics and reporting
    - Escalation procedures
    - Review history and audit trail
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize review system"""
        self.config = config or {}
        
        # Review configuration
        self.criteria = ReviewCriteria(**self.config.get('review_criteria', {}))
        self.reviewers = self.config.get('reviewers', [])
        self.escalation_rules = self.config.get('escalation_rules', {})
        
        # Review state
        self.pending_reviews: Dict[str, ReviewItem] = {}
        self.completed_reviews: Dict[str, ReviewItem] = {}
        self.review_decisions: Dict[str, ReviewDecision] = {}
        
        # Statistics
        self.review_stats = {
            'total_reviews': 0,
            'automated_approvals': 0,
            'manual_reviews': 0,
            'rejections': 0,
            'escalations': 0,
            'average_review_time': 0.0,
            'average_quality_score': 0.0
        }
        
        # Callbacks
        self.review_callbacks: List[Callable[[ReviewItem], Any]] = []
        self.approval_callbacks: List[Callable[[ReviewItem], Any]] = []
        self.rejection_callbacks: List[Callable[[ReviewItem], Any]] = []
        self.escalation_callbacks: List[Callable[[ReviewItem], Any]] = []
    
    def submit_for_review(self, cv_file: CVFile, extraction_result: ExtractionResult, 
                          cv_data: CVData, validation_report: ValidationReport,
                          processing_time: float = 0.0) -> str:
        """
        Submit item for review
        
        Args:
            cv_file: Original CV file
            extraction_result: Text extraction result
            cv_data: Parsed CV data
            validation_report: Validation results
            processing_time: Time taken to process
            
        Returns:
            Review item ID
        """
        # Generate review ID
        review_id = self._generate_review_id(cv_file)
        
        # Calculate quality score
        quality_score = validation_report.overall_score
        
        # Determine review type
        review_type = self._determine_review_type(validation_report, quality_score)
        
        # Create review item
        review_item = ReviewItem(
            id=review_id,
            cv_file=cv_file,
            extraction_result=extraction_result,
            cv_data=cv_data,
            validation_report=validation_report,
            review_type=review_type,
            quality_score=quality_score,
            processing_time=processing_time
        )
        
        # Add to pending reviews
        self.pending_reviews[review_id] = review_item
        self.review_stats['total_reviews'] += 1
        
        # Auto-review if criteria met
        if review_type == ReviewType.AUTOMATED:
            self._perform_automated_review(review_item)
        else:
            # Assign for manual review
            self._assign_manual_review(review_item)
        
        self._log(f"Submitted {review_id} for {review_type.value} review (score: {quality_score:.2f})")
        return review_id
    
    def _determine_review_type(self, validation_report: ValidationReport, 
                              quality_score: float) -> ReviewType:
        """Determine type of review needed"""
        # Check for critical issues
        if validation_report.critical_issues > 0:
            return ReviewType.MANUAL
        
        # Check quality score thresholds
        if quality_score >= self.criteria.auto_approve_threshold:
            return ReviewType.AUTOMATED
        elif quality_score < self.criteria.escalation_threshold:
            return ReviewType.MANAGER
        elif self.criteria.require_manual_review:
            return ReviewType.MANUAL
        else:
            return ReviewType.AUTOMATED
    
    def _perform_automated_review(self, review_item: ReviewItem):
        """Perform automated review"""
        quality_score = review_item.quality_score
        
        # Determine decision based on criteria
        if quality_score >= self.criteria.min_quality_score:
            decision = ReviewStatus.APPROVED
            self.review_stats['automated_approvals'] += 1
        else:
            decision = ReviewStatus.REJECTED
            self.review_stats['rejections'] += 1
        
        # Create decision
        review_decision = ReviewDecision(
            review_item_id=review_item.id,
            decision=decision,
            reviewer="AUTOMATED_SYSTEM",
            notes=[f"Automated review - Quality score: {quality_score:.2f}"],
            quality_score=quality_score
        )
        
        # Process decision
        self._process_review_decision(review_item, review_decision)
    
    def _assign_manual_review(self, review_item: ReviewItem):
        """Assign item for manual review"""
        # Find available reviewer
        assigned_reviewer = self._find_available_reviewer()
        
        if assigned_reviewer:
            review_item.assigned_to = assigned_reviewer
            review_item.review_status = ReviewStatus.IN_PROGRESS
            self.review_stats['manual_reviews'] += 1
            
            # Notify reviewer
            self._notify_reviewer(review_item)
        else:
            # Escalate if no reviewers available
            self._escalate_review(review_item)
    
    def _find_available_reviewer(self) -> Optional[str]:
        """Find available reviewer"""
        if not self.reviewers:
            return None
        
        # Simple round-robin assignment
        # In production, this could be more sophisticated
        for reviewer in self.reviewers:
            # Check reviewer workload
            reviewer_load = self._get_reviewer_load(reviewer)
            if reviewer_load < 5:  # Max 5 reviews per reviewer
                return reviewer
        
        return None
    
    def _get_reviewer_load(self, reviewer: str) -> int:
        """Get current workload for reviewer"""
        return sum(1 for item in self.pending_reviews.values() 
                  if item.assigned_to == reviewer and item.review_status == ReviewStatus.IN_PROGRESS)
    
    def _escalate_review(self, review_item: ReviewItem):
        """Escalate review to higher level"""
        review_item.review_status = ReviewStatus.ESCALATED
        review_item.review_type = ReviewType.MANAGER
        self.review_stats['escalations'] += 1
        
        # Call escalation callbacks
        for callback in self.escalation_callbacks:
            try:
                callback(review_item)
            except Exception as e:
                self._log(f"Escalation callback error: {str(e)}", "ERROR")
        
        self._log(f"Escalated review {review_item.id} to manager level")
    
    def submit_review_decision(self, review_id: str, reviewer: str, 
                               decision: ReviewStatus, notes: List[str],
                               quality_score: float, feedback: Dict[str, Any] = None):
        """
        Submit manual review decision
        
        Args:
            review_id: Review item ID
            reviewer: Reviewer name
            decision: Review decision
            notes: Reviewer notes
            quality_score: Quality score assessment
            feedback: Additional feedback
        """
        if review_id not in self.pending_reviews:
            raise ValueError(f"Review {review_id} not found")
        
        review_item = self.pending_reviews[review_id]
        
        # Create decision
        review_decision = ReviewDecision(
            review_item_id=review_id,
            decision=decision,
            reviewer=reviewer,
            notes=notes,
            quality_score=quality_score,
            feedback=feedback or {}
        )
        
        # Process decision
        self._process_review_decision(review_item, review_decision)
    
    def _process_review_decision(self, review_item: ReviewItem, decision: ReviewDecision):
        """Process review decision"""
        # Update review item
        review_item.review_status = decision.decision
        review_item.reviewed_at = decision.timestamp
        review_item.reviewer_notes = decision.notes
        review_item.quality_score = decision.quality_score
        
        # Store decision
        self.review_decisions[review_item.id] = decision
        
        # Move to completed reviews
        self.completed_reviews[review_item.id] = review_item
        del self.pending_reviews[review_item.id]
        
        # Update statistics
        self._update_review_statistics(review_item, decision)
        
        # Call appropriate callbacks
        if decision.decision == ReviewStatus.APPROVED:
            for callback in self.approval_callbacks:
                try:
                    callback(review_item)
                except Exception as e:
                    self._log(f"Approval callback error: {str(e)}", "ERROR")
        elif decision.decision == ReviewStatus.REJECTED:
            for callback in self.rejection_callbacks:
                try:
                    callback(review_item)
                except Exception as e:
                    self._log(f"Rejection callback error: {str(e)}", "ERROR")
        
        self._log(f"Processed review decision for {review_item.id}: {decision.decision.value}")
    
    def _update_review_statistics(self, review_item: ReviewItem, decision: ReviewDecision):
        """Update review statistics"""
        # Calculate review time
        review_time = (decision.timestamp - review_item.created_at).total_seconds()
        
        # Update average review time
        total_reviews = self.review_stats['total_reviews']
        current_avg = self.review_stats['average_review_time']
        self.review_stats['average_review_time'] = (
            (current_avg * (total_reviews - 1) + review_time) / total_reviews
        )
        
        # Update average quality score
        current_avg_score = self.review_stats['average_quality_score']
        self.review_stats['average_quality_score'] = (
            (current_avg_score * (total_reviews - 1) + decision.quality_score) / total_reviews
        )
    
    def get_pending_reviews(self, reviewer: Optional[str] = None) -> List[ReviewItem]:
        """Get pending reviews, optionally filtered by reviewer"""
        if reviewer:
            return [item for item in self.pending_reviews.values() 
                   if item.assigned_to == reviewer]
        return list(self.pending_reviews.values())
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """Get comprehensive review statistics"""
        return {
            'total_reviews': self.review_stats['total_reviews'],
            'pending_reviews': len(self.pending_reviews),
            'completed_reviews': len(self.completed_reviews),
            'automated_approvals': self.review_stats['automated_approvals'],
            'manual_reviews': self.review_stats['manual_reviews'],
            'rejections': self.review_stats['rejections'],
            'escalations': self.review_stats['escalations'],
            'average_review_time_seconds': self.review_stats['average_review_time'],
            'average_quality_score': self.review_stats['average_quality_score'],
            'approval_rate': (
                self.review_stats['automated_approvals'] / self.review_stats['total_reviews']
                if self.review_stats['total_reviews'] > 0 else 0
            ),
            'reviewer_load': {
                reviewer: self._get_reviewer_load(reviewer) 
                for reviewer in self.reviewers
            }
        }
    
    def get_review_history(self, limit: int = 100) -> List[ReviewItem]:
        """Get review history"""
        # Sort by completion time (most recent first)
        completed_items = sorted(
            self.completed_reviews.values(),
            key=lambda x: x.reviewed_at or x.created_at,
            reverse=True
        )
        return completed_items[:limit]
    
    def export_review_report(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Export comprehensive review report"""
        # Filter by date range
        reviews = self.get_review_history()
        if start_date:
            reviews = [r for r in reviews if r.created_at >= start_date]
        if end_date:
            reviews = [r for r in reviews if r.created_at <= end_date]
        
        # Generate report
        report = {
            'report_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'generated_at': datetime.now().isoformat()
            },
            'summary': self.get_review_statistics(),
            'reviews': []
        }
        
        # Add review details
        for review in reviews:
            decision = self.review_decisions.get(review.id)
            review_data = {
                'id': review.id,
                'file_name': review.cv_file.file_name,
                'review_type': review.review_type.value,
                'review_status': review.review_status.value,
                'quality_score': review.quality_score,
                'processing_time': review.processing_time,
                'created_at': review.created_at.isoformat(),
                'reviewed_at': review.reviewed_at.isoformat() if review.reviewed_at else None,
                'assigned_to': review.assigned_to,
                'reviewer_notes': review.reviewer_notes,
                'validation_summary': {
                    'overall_score': review.validation_report.overall_score,
                    'critical_issues': review.validation_report.critical_issues,
                    'warnings': review.validation_report.warnings
                }
            }
            
            if decision:
                review_data['decision'] = {
                    'status': decision.decision.value,
                    'reviewer': decision.reviewer,
                    'notes': decision.notes,
                    'timestamp': decision.timestamp.isoformat()
                }
            
            report['reviews'].append(review_data)
        
        return report
    
    def add_review_callback(self, callback: Callable[[ReviewItem], Any]):
        """Add callback for review events"""
        self.review_callbacks.append(callback)
    
    def add_approval_callback(self, callback: Callable[[ReviewItem], Any]):
        """Add callback for approval events"""
        self.approval_callbacks.append(callback)
    
    def add_rejection_callback(self, callback: Callable[[ReviewItem], Any]):
        """Add callback for rejection events"""
        self.rejection_callbacks.append(callback)
    
    def add_escalation_callback(self, callback: Callable[[ReviewItem], Any]):
        """Add callback for escalation events"""
        self.escalation_callbacks.append(callback)
    
    def _generate_review_id(self, cv_file: CVFile) -> str:
        """Generate unique review ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = cv_file.file_name.replace(' ', '_')[:20]
        return f"REV_{timestamp}_{file_hash}"
    
    def _notify_reviewer(self, review_item: ReviewItem):
        """Notify reviewer of new assignment"""
        # In production, this would send email/notification
        self._log(f"Notified reviewer {review_item.assigned_to} of review {review_item.id}")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [ReviewSystem] {message}")
