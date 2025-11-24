#!/usr/bin/env python3
"""
Database Abstraction Layer
Generic database interface supporting SQLite and PostgreSQL
"""

import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from src.core.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


# ============================================================================
# DATABASE MODELS (Generic - no CV-specific data)
# ============================================================================

class CVFileRecord(Base):
    """Record of processed CV files"""
    __tablename__ = 'cv_files'
    
    id = Column(String(50), primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_format = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    
    # Timestamps
    added_date = Column(DateTime, default=datetime.now)
    processed_date = Column(DateTime, nullable=True)
    
    # Results
    confidence_score = Column(Float, default=0.0)
    strategy_used = Column(String(50), nullable=True)
    needs_review = Column(Boolean, default=False)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)


class ProcessingResult(Base):
    """Results of CV processing"""
    __tablename__ = 'processing_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cv_id = Column(String(50), nullable=False, index=True)
    
    # Processing details
    processing_time = Column(Float, nullable=False)
    extraction_success = Column(Boolean, nullable=False)
    parsing_success = Column(Boolean, nullable=False)
    generation_success = Column(Boolean, nullable=False)
    
    # Quality metrics
    confidence_score = Column(Float, default=0.0)
    validation_issues = Column(JSON, nullable=True)
    
    # Output
    output_file_path = Column(String(512), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.now)


class BatchJob(Base):
    """Track batch processing jobs"""
    __tablename__ = 'batch_jobs'
    
    id = Column(String(50), primary_key=True)
    
    # Job details
    total_files = Column(Integer, nullable=False)
    processed_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), nullable=False, default='pending')
    current_file = Column(String(255), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Performance
    average_time_per_file = Column(Float, default=0.0)
    average_confidence = Column(Float, default=0.0)


class APIKey(Base):
    """API authentication keys"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    
    # Usage tracking
    created_at = Column(DateTime, default=datetime.now)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Permissions
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # requests per minute
    daily_limit = Column(Integer, default=1000)  # CVs per day


class FeedbackLog(Base):
    """Log manual corrections for quality improvement"""
    __tablename__ = 'feedback_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cv_id = Column(String(50), nullable=False, index=True)
    
    # Correction details
    field_corrected = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=True)
    
    # Metadata
    corrected_by = Column(String(100), nullable=True)
    correction_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """
    Generic database manager supporting SQLite and PostgreSQL
    Uses environment variables for configuration
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            db_url: Database URL (if None, reads from environment or uses default SQLite)
        """
        self.logger = setup_logger(__name__)
        
        # Determine database URL
        if db_url:
            self.db_url = db_url
        else:
            # Try to get from environment
            self.db_url = os.getenv('DATABASE_URL')
            
            if not self.db_url:
                # Default to SQLite
                db_dir = 'database'
                os.makedirs(db_dir, exist_ok=True)
                db_path = os.path.join(db_dir, 'cv_automation.db')
                self.db_url = f'sqlite:///{db_path}'
        
        self.logger.info(f"Initializing database: {self.db_url.split('://')[0]}://...")
        
        # Create engine
        self.engine = create_engine(
            self.db_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True  # Verify connections before using
        )
        
        # Create session factory
        self.SessionFactory = sessionmaker(bind=self.engine)
        
        # Create tables
        self.create_tables()
        
        self.logger.info("Database initialized successfully")
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(self.engine)
        self.logger.info("Database tables created/verified")
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    # ========================================================================
    # CV FILES OPERATIONS
    # ========================================================================
    
    def add_cv_file(self, cv_file_data: Dict) -> str:
        """
        Add a new CV file record
        Returns the CV ID
        """
        with self.session_scope() as session:
            cv_record = CVFileRecord(**cv_file_data)
            session.add(cv_record)
            session.flush()  # Flush to ensure ID is available
            return cv_record.id
    
    def update_cv_file(self, cv_id: str, updates: Dict):
        """Update CV file record"""
        with self.session_scope() as session:
            cv_record = session.query(CVFileRecord).filter_by(id=cv_id).first()
            if cv_record:
                for key, value in updates.items():
                    setattr(cv_record, key, value)
    
    def get_cv_file(self, cv_id: str) -> Optional[Dict]:
        """Get CV file record by ID as dictionary"""
        with self.session_scope() as session:
            record = session.query(CVFileRecord).filter_by(id=cv_id).first()
            if not record:
                return None
            # Convert to dict to avoid detached session issues
            return {
                'id': record.id,
                'file_name': record.file_name,
                'file_path': record.file_path,
                'file_format': record.file_format,
                'file_size': record.file_size,
                'status': record.status,
                'confidence_score': record.confidence_score,
                'strategy_used': record.strategy_used,
                'needs_review': record.needs_review,
                'error_message': record.error_message,
                'added_date': record.added_date,
                'processed_date': record.processed_date
            }
    
    def get_all_cv_files(self, limit: Optional[int] = None) -> List[CVFileRecord]:
        """Get all CV file records"""
        with self.session_scope() as session:
            query = session.query(CVFileRecord).order_by(CVFileRecord.added_date.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
    
    # ========================================================================
    # PROCESSING RESULTS OPERATIONS
    # ========================================================================
    
    def add_processing_result(self, result_data: Dict) -> ProcessingResult:
        """Add processing result"""
        with self.session_scope() as session:
            result = ProcessingResult(**result_data)
            session.add(result)
            return result
    
    def get_processing_results(self, cv_id: str) -> List[ProcessingResult]:
        """Get all processing results for a CV"""
        with self.session_scope() as session:
            return session.query(ProcessingResult).filter_by(cv_id=cv_id).all()
    
    # ========================================================================
    # BATCH JOBS OPERATIONS
    # ========================================================================
    
    def create_batch_job(self, batch_data: Dict) -> BatchJob:
        """Create new batch job"""
        with self.session_scope() as session:
            batch = BatchJob(**batch_data)
            session.add(batch)
            return batch
    
    def update_batch_job(self, batch_id: str, updates: Dict):
        """Update batch job"""
        with self.session_scope() as session:
            batch = session.query(BatchJob).filter_by(id=batch_id).first()
            if batch:
                for key, value in updates.items():
                    setattr(batch, key, value)
    
    def get_batch_job(self, batch_id: str) -> Optional[Dict]:
        """Get batch job by ID as dictionary"""
        with self.session_scope() as session:
            record = session.query(BatchJob).filter_by(id=batch_id).first()
            if not record:
                return None
            return {
                'id': record.id,
                'total_files': record.total_files,
                'processed_files': record.processed_files,
                'successful_files': record.successful_files,
                'failed_files': record.failed_files,
                'status': record.status,
                'current_file': record.current_file,
                'started_at': record.started_at,
                'completed_at': record.completed_at,
                'average_time_per_file': record.average_time_per_file,
                'average_confidence': record.average_confidence
            }
    
    def get_active_batch_jobs(self) -> List[BatchJob]:
        """Get all active batch jobs"""
        with self.session_scope() as session:
            return session.query(BatchJob).filter_by(status='processing').all()
    
    # ========================================================================
    # API KEYS OPERATIONS
    # ========================================================================
    
    def create_api_key(self, key_data: Dict) -> APIKey:
        """Create new API key"""
        with self.session_scope() as session:
            api_key = APIKey(**key_data)
            session.add(api_key)
            return api_key
    
    def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict]:
        """Get API key by hash as dictionary"""
        with self.session_scope() as session:
            record = session.query(APIKey).filter_by(key_hash=key_hash, is_active=True).first()
            if not record:
                return None
            return {
                'id': record.id,
                'key_name': record.key_name,
                'key_hash': record.key_hash,
                'is_active': record.is_active,
                'rate_limit': record.rate_limit,
                'daily_limit': record.daily_limit,
                'created_at': record.created_at,
                'last_used_at': record.last_used_at,
                'usage_count': record.usage_count
            }
    
    def update_api_key_usage(self, key_hash: str):
        """Update API key usage statistics"""
        with self.session_scope() as session:
            api_key = session.query(APIKey).filter_by(key_hash=key_hash).first()
            if api_key:
                api_key.last_used_at = datetime.now()
                api_key.usage_count += 1
    
    # ========================================================================
    # FEEDBACK LOG OPERATIONS
    # ========================================================================
    
    def log_correction(self, correction_data: Dict) -> FeedbackLog:
        """Log a manual correction"""
        with self.session_scope() as session:
            feedback = FeedbackLog(**correction_data)
            session.add(feedback)
            return feedback
    
    def get_corrections(self, cv_id: Optional[str] = None, limit: int = 100) -> List[FeedbackLog]:
        """Get feedback corrections"""
        with self.session_scope() as session:
            query = session.query(FeedbackLog)
            if cv_id:
                query = query.filter_by(cv_id=cv_id)
            return query.order_by(FeedbackLog.timestamp.desc()).limit(limit).all()
    
    # ========================================================================
    # DASHBOARD & ANALYTICS OPERATIONS (Generic queries)
    # ========================================================================
    
    def get_processing_stats(self, days: int = 30) -> Dict:
        """Get processing statistics for dashboard"""
        with self.session_scope() as session:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)
            
            # Generic count queries
            total_processed = session.query(CVFileRecord).filter(
                CVFileRecord.processed_date >= start_date
            ).count()
            
            successful = session.query(CVFileRecord).filter(
                CVFileRecord.processed_date >= start_date,
                CVFileRecord.status == 'completed'
            ).count()
            
            failed = session.query(CVFileRecord).filter(
                CVFileRecord.processed_date >= start_date,
                CVFileRecord.status == 'failed'
            ).count()
            
            return {
                'total_processed': total_processed,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total_processed * 100) if total_processed > 0 else 0
            }
    
    def get_confidence_distribution(self) -> Dict:
        """Get confidence score distribution"""
        with self.session_scope() as session:
            results = session.query(CVFileRecord.confidence_score).filter(
                CVFileRecord.confidence_score > 0
            ).all()
            
            scores = [r[0] for r in results]
            
            if not scores:
                return {'bins': {}, 'average': 0}
            
            # Calculate distribution
            bins = {
                'excellent': len([s for s in scores if s >= 0.9]),
                'good': len([s for s in scores if 0.7 <= s < 0.9]),
                'acceptable': len([s for s in scores if 0.5 <= s < 0.7]),
                'poor': len([s for s in scores if 0.3 <= s < 0.5]),
                'failed': len([s for s in scores if s < 0.3])
            }
            
            return {
                'bins': bins,
                'average': sum(scores) / len(scores)
            }
    
    def get_recent_activity(self, limit: int = 50) -> List[Dict]:
        """Get recent processing activity"""
        with self.session_scope() as session:
            records = session.query(CVFileRecord).order_by(
                CVFileRecord.processed_date.desc()
            ).limit(limit).all()
            
            return [{
                'file_name': r.file_name,
                'status': r.status,
                'confidence': r.confidence_score,
                'processed_date': r.processed_date.isoformat() if r.processed_date else None
            } for r in records]
    
    def get_failed_cvs(self) -> List[Dict]:
        """Get list of failed CVs"""
        with self.session_scope() as session:
            failed = session.query(CVFileRecord).filter_by(status='failed').all()
            
            return [{
                'id': r.id,
                'file_name': r.file_name,
                'error_message': r.error_message,
                'processed_date': r.processed_date.isoformat() if r.processed_date else None
            } for r in failed]


# ============================================================================
# GLOBAL DATABASE INSTANCE (Singleton pattern)
# ============================================================================

_db_instance = None

def get_database() -> DatabaseManager:
    """Get global database instance (singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance


# Export main classes
__all__ = ['DatabaseManager', 'get_database', 'CVFileRecord', 'ProcessingResult', 
           'BatchJob', 'APIKey', 'FeedbackLog']

