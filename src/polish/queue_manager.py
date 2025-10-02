#!/usr/bin/env python3
"""
Queue Manager - Processing queue and priority handling
Generic queue management system with priority, scheduling, and load balancing
"""

import heapq
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Generator
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from src.core import CVFile
from .file_scanner import FileMetadata, ScanStatus


class Priority(str, Enum):
    """Processing priority levels"""
    CRITICAL = "critical"    # 1 - Immediate processing
    HIGH = "high"           # 2 - High priority
    NORMAL = "normal"       # 5 - Standard priority
    LOW = "low"            # 8 - Low priority
    BACKGROUND = "background"  # 10 - Background processing


class QueueStatus(str, Enum):
    """Queue item status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class QueueItem:
    """Item in processing queue"""
    id: str
    file_metadata: FileMetadata
    priority: Priority
    status: QueueStatus = QueueStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For heapq priority queue"""
        priority_order = {
            Priority.CRITICAL: 1,
            Priority.HIGH: 2,
            Priority.NORMAL: 5,
            Priority.LOW: 8,
            Priority.BACKGROUND: 10
        }
        return priority_order[self.priority] < priority_order[other.priority]


@dataclass
class QueueStatistics:
    """Queue processing statistics"""
    total_items: int = 0
    pending_items: int = 0
    processing_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    cancelled_items: int = 0
    average_processing_time: float = 0.0
    success_rate: float = 0.0
    throughput_per_hour: float = 0.0
    queue_depth: int = 0
    estimated_completion_time: Optional[datetime] = None


class QueueManager:
    """
    Generic queue management system with advanced features
    
    Features:
    - Priority-based processing
    - Load balancing
    - Retry logic with exponential backoff
    - Progress tracking
    - Queue statistics
    - Dynamic priority adjustment
    - Batch processing
    - Resource management
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize queue manager"""
        self.config = config or {}
        
        # Queue configuration
        self.max_concurrent_items = self.config.get('max_concurrent_items', 5)
        self.max_queue_size = self.config.get('max_queue_size', 1000)
        self.retry_delay_base = self.config.get('retry_delay_base', 60)  # seconds
        self.max_retry_delay = self.config.get('max_retry_delay', 3600)  # 1 hour
        
        # Queue state
        self.priority_queue: List[QueueItem] = []  # heapq priority queue
        self.processing_items: Dict[str, QueueItem] = {}
        self.completed_items: Dict[str, QueueItem] = {}
        self.failed_items: Dict[str, QueueItem] = {}
        self.item_lookup: Dict[str, QueueItem] = {}  # Quick lookup by ID
        
        # Statistics
        self.stats = QueueStatistics()
        self.processing_times: deque = deque(maxlen=100)  # Keep last 100 processing times
        
        # Threading
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        
        # Callbacks
        self.processing_callbacks: List[Callable[[QueueItem], Any]] = []
        self.completion_callbacks: List[Callable[[QueueItem], Any]] = []
        self.failure_callbacks: List[Callable[[QueueItem], Any]] = []
    
    def add_item(self, file_metadata: FileMetadata, priority: Priority = Priority.NORMAL, 
                 metadata: Dict[str, Any] = None) -> str:
        """
        Add item to processing queue
        
        Args:
            file_metadata: File metadata to process
            priority: Processing priority
            metadata: Additional metadata
            
        Returns:
            Queue item ID
        """
        with self.lock:
            if len(self.item_lookup) >= self.max_queue_size:
                raise Exception(f"Queue is full (max {self.max_queue_size} items)")
            
            # Generate unique ID
            item_id = self._generate_item_id(file_metadata)
            
            # Create queue item
            queue_item = QueueItem(
                id=item_id,
                file_metadata=file_metadata,
                priority=priority,
                metadata=metadata or {}
            )
            
            # Add to queue
            heapq.heappush(self.priority_queue, queue_item)
            self.item_lookup[item_id] = queue_item
            self.stats.total_items += 1
            self.stats.pending_items += 1
            
            # Notify waiting threads
            self.condition.notify()
            
            self._log(f"Added item {item_id} to queue (priority: {priority.value})")
            return item_id
    
    def add_batch(self, file_metadata_list: List[FileMetadata], 
                  priority: Priority = Priority.NORMAL) -> List[str]:
        """Add multiple items to queue in batch"""
        item_ids = []
        for metadata in file_metadata_list:
            try:
                item_id = self.add_item(metadata, priority)
                item_ids.append(item_id)
            except Exception as e:
                self._log(f"Failed to add item {metadata.file_name}: {str(e)}", "ERROR")
        
        self._log(f"Added batch of {len(item_ids)} items to queue")
        return item_ids
    
    def get_next_item(self, timeout: Optional[float] = None) -> Optional[QueueItem]:
        """
        Get next item from queue for processing
        
        Args:
            timeout: Maximum time to wait for an item
            
        Returns:
            Next queue item or None if timeout/empty
        """
        with self.condition:
            # Wait for available item
            if not self.priority_queue:
                if timeout is None:
                    self.condition.wait()
                else:
                    self.condition.wait(timeout)
            
            # Check if we have capacity
            if len(self.processing_items) >= self.max_concurrent_items:
                return None
            
            # Get next item
            if self.priority_queue:
                item = heapq.heappop(self.priority_queue)
                item.status = QueueStatus.PROCESSING
                item.started_at = datetime.now()
                
                self.processing_items[item.id] = item
                self.stats.pending_items -= 1
                self.stats.processing_items += 1
                
                self._log(f"Started processing item {item.id}")
                return item
        
        return None
    
    def complete_item(self, item_id: str, success: bool = True, 
                     error_message: Optional[str] = None, 
                     processing_time: Optional[float] = None):
        """
        Mark item as completed
        
        Args:
            item_id: Queue item ID
            success: Whether processing was successful
            error_message: Error message if failed
            processing_time: Time taken to process
        """
        with self.lock:
            if item_id not in self.item_lookup:
                self._log(f"Item {item_id} not found", "ERROR")
                return
            
            item = self.item_lookup[item_id]
            
            # Update item
            item.completed_at = datetime.now()
            item.processing_time = processing_time
            item.error_message = error_message
            
            if success:
                item.status = QueueStatus.COMPLETED
                self.completed_items[item_id] = item
                self.stats.completed_items += 1
                
                # Update processing time statistics
                if processing_time:
                    self.processing_times.append(processing_time)
                    self.stats.average_processing_time = sum(self.processing_times) / len(self.processing_times)
                
                # Call completion callbacks
                for callback in self.completion_callbacks:
                    try:
                        callback(item)
                    except Exception as e:
                        self._log(f"Completion callback error: {str(e)}", "ERROR")
            else:
                # Handle retry logic
                if item.retry_count < item.max_retries:
                    item.status = QueueStatus.RETRYING
                    item.retry_count += 1
                    
                    # Calculate retry delay with exponential backoff
                    retry_delay = min(
                        self.retry_delay_base * (2 ** (item.retry_count - 1)),
                        self.max_retry_delay
                    )
                    
                    # Schedule retry
                    retry_time = datetime.now() + timedelta(seconds=retry_delay)
                    item.metadata['retry_time'] = retry_time
                    
                    # Re-add to queue with higher priority
                    heapq.heappush(self.priority_queue, item)
                    self.stats.pending_items += 1
                    
                    self._log(f"Item {item_id} scheduled for retry {item.retry_count}/{item.max_retries} at {retry_time}")
                else:
                    item.status = QueueStatus.FAILED
                    self.failed_items[item_id] = item
                    self.stats.failed_items += 1
                    
                    # Call failure callbacks
                    for callback in self.failure_callbacks:
                        try:
                            callback(item)
                        except Exception as e:
                            self._log(f"Failure callback error: {str(e)}", "ERROR")
            
            # Remove from processing
            if item_id in self.processing_items:
                del self.processing_items[item_id]
                self.stats.processing_items -= 1
            
            # Update success rate
            total_processed = self.stats.completed_items + self.stats.failed_items
            if total_processed > 0:
                self.stats.success_rate = self.stats.completed_items / total_processed
            
            # Update throughput
            self._update_throughput()
            
            self._log(f"Completed item {item_id} (success: {success})")
    
    def cancel_item(self, item_id: str) -> bool:
        """Cancel a pending or processing item"""
        with self.lock:
            if item_id not in self.item_lookup:
                return False
            
            item = self.item_lookup[item_id]
            
            if item.status == QueueStatus.PENDING:
                # Remove from priority queue
                self.priority_queue = [i for i in self.priority_queue if i.id != item_id]
                heapq.heapify(self.priority_queue)
                self.stats.pending_items -= 1
            elif item.status == QueueStatus.PROCESSING:
                # Mark as cancelled but let it finish
                item.status = QueueStatus.CANCELLED
                self.stats.processing_items -= 1
            
            item.status = QueueStatus.CANCELLED
            self.stats.cancelled_items += 1
            
            self._log(f"Cancelled item {item_id}")
            return True
    
    def get_item_status(self, item_id: str) -> Optional[QueueStatus]:
        """Get status of specific item"""
        with self.lock:
            if item_id in self.item_lookup:
                return self.item_lookup[item_id].status
            return None
    
    def get_queue_statistics(self) -> QueueStatistics:
        """Get comprehensive queue statistics"""
        with self.lock:
            # Update dynamic statistics
            self.stats.queue_depth = len(self.priority_queue)
            self.stats.estimated_completion_time = self._estimate_completion_time()
            
            return QueueStatistics(
                total_items=self.stats.total_items,
                pending_items=self.stats.pending_items,
                processing_items=self.stats.processing_items,
                completed_items=self.stats.completed_items,
                failed_items=self.stats.failed_items,
                cancelled_items=self.stats.cancelled_items,
                average_processing_time=self.stats.average_processing_time,
                success_rate=self.stats.success_rate,
                throughput_per_hour=self.stats.throughput_per_hour,
                queue_depth=self.stats.queue_depth,
                estimated_completion_time=self.stats.estimated_completion_time
            )
    
    def get_items_by_status(self, status: QueueStatus) -> List[QueueItem]:
        """Get all items with specific status"""
        with self.lock:
            return [item for item in self.item_lookup.values() if item.status == status]
    
    def get_items_by_priority(self, priority: Priority) -> List[QueueItem]:
        """Get all items with specific priority"""
        with self.lock:
            return [item for item in self.item_lookup.values() if item.priority == priority]
    
    def clear_completed_items(self, older_than_hours: int = 24):
        """Clear completed items older than specified hours"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            # Clear completed items
            old_completed = [
                item_id for item_id, item in self.completed_items.items()
                if item.completed_at and item.completed_at < cutoff_time
            ]
            
            for item_id in old_completed:
                del self.completed_items[item_id]
                del self.item_lookup[item_id]
            
            # Clear failed items
            old_failed = [
                item_id for item_id, item in self.failed_items.items()
                if item.completed_at and item.completed_at < cutoff_time
            ]
            
            for item_id in old_failed:
                del self.failed_items[item_id]
                del self.item_lookup[item_id]
            
            self._log(f"Cleared {len(old_completed)} completed and {len(old_failed)} failed items")
    
    def add_processing_callback(self, callback: Callable[[QueueItem], Any]):
        """Add callback for when item starts processing"""
        self.processing_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[QueueItem], Any]):
        """Add callback for when item completes successfully"""
        self.completion_callbacks.append(callback)
    
    def add_failure_callback(self, callback: Callable[[QueueItem], Any]):
        """Add callback for when item fails"""
        self.failure_callbacks.append(callback)
    
    def _generate_item_id(self, file_metadata: FileMetadata) -> str:
        """Generate unique item ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = file_metadata.checksum[:8]
        return f"{timestamp}_{file_hash}"
    
    def _update_throughput(self):
        """Update throughput statistics"""
        if not self.processing_times:
            return
        
        # Calculate average processing time
        avg_time = sum(self.processing_times) / len(self.processing_times)
        
        # Estimate throughput (items per hour)
        if avg_time > 0:
            self.stats.throughput_per_hour = 3600 / avg_time
    
    def _estimate_completion_time(self) -> Optional[datetime]:
        """Estimate when queue will be empty"""
        if not self.priority_queue or not self.processing_times:
            return None
        
        # Estimate based on current throughput
        remaining_items = len(self.priority_queue)
        if self.stats.throughput_per_hour > 0:
            hours_to_complete = remaining_items / self.stats.throughput_per_hour
            return datetime.now() + timedelta(hours=hours_to_complete)
        
        return None
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [QueueManager] {message}")
