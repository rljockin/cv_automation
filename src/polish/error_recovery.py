#!/usr/bin/env python3
"""
Error Recovery - Robust error handling and retry logic
Generic error recovery system with retry strategies, circuit breakers, and fallback mechanisms
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum

from src.core import CVFile, CVAutomationException


class RetryStrategy(str, Enum):
    """Retry strategies"""
    FIXED = "fixed"              # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"           # Linear backoff
    RANDOM = "random"           # Random jitter


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    retryable_exceptions: List[Type[Exception]] = field(default_factory=list)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    success_threshold: int = 3
    timeout: float = 30.0  # seconds


@dataclass
class ErrorContext:
    """Error context information"""
    operation: str
    file_path: Optional[str] = None
    attempt_number: int = 1
    total_attempts: int = 1
    error_type: str = ""
    error_message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        self.success_count += 1
        self.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.success_count = 0


class ErrorRecovery:
    """
    Generic error recovery system with comprehensive retry and fallback mechanisms
    
    Features:
    - Multiple retry strategies
    - Circuit breaker pattern
    - Fallback mechanisms
    - Error classification
    - Recovery tracking
    - Performance monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize error recovery system"""
        self.config = config or {}
        
        # Default configurations
        self.default_retry_config = RetryConfig(**self.config.get('retry_config', {}))
        self.default_circuit_config = CircuitBreakerConfig(**self.config.get('circuit_config', {}))
        
        # Circuit breakers by operation type
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Error tracking
        self.error_history: List[ErrorContext] = []
        self.recovery_stats = {
            'total_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'circuit_breaker_trips': 0
        }
        
        # Fallback functions
        self.fallback_functions: Dict[str, Callable] = {}
        
        # Callbacks
        self.error_callbacks: List[Callable[[ErrorContext], Any]] = []
        self.recovery_callbacks: List[Callable[[ErrorContext], Any]] = []
    
    def retry_with_strategy(self, func: Callable, *args, retry_config: RetryConfig = None,
                          operation_name: str = "unknown", **kwargs) -> Any:
        """
        Execute function with retry strategy
        
        Args:
            func: Function to execute
            *args: Function arguments
            retry_config: Retry configuration
            operation_name: Name of operation for tracking
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        config = retry_config or self.default_retry_config
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                # Check circuit breaker
                circuit_breaker = self._get_circuit_breaker(operation_name)
                if circuit_breaker:
                    return circuit_breaker.call(func, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                # Create error context
                error_context = ErrorContext(
                    operation=operation_name,
                    attempt_number=attempt,
                    total_attempts=config.max_attempts,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    metadata={'args': str(args), 'kwargs': str(kwargs)}
                )
                
                # Record error
                self._record_error(error_context)
                
                # Check if error is retryable
                if not self._is_retryable_error(e, config):
                    break
                
                # If this is the last attempt, don't wait
                if attempt == config.max_attempts:
                    break
                
                # Calculate delay
                delay = self._calculate_delay(attempt, config)
                
                # Wait before retry
                time.sleep(delay)
        
        # All retries failed
        self.recovery_stats['failed_recoveries'] += 1
        
        # Try fallback if available
        if operation_name in self.fallback_functions:
            try:
                fallback_result = self.fallback_functions[operation_name](*args, **kwargs)
                self._log(f"Fallback succeeded for {operation_name}")
                return fallback_result
            except Exception as fallback_error:
                self._log(f"Fallback also failed for {operation_name}: {str(fallback_error)}", "ERROR")
        
        # Re-raise last exception
        raise last_exception
    
    def _get_circuit_breaker(self, operation_name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker for operation"""
        if operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreaker(
                operation_name, self.default_circuit_config
            )
        return self.circuit_breakers[operation_name]
    
    def _is_retryable_error(self, error: Exception, config: RetryConfig) -> bool:
        """Check if error is retryable"""
        # Check configured retryable exceptions
        if config.retryable_exceptions:
            return any(isinstance(error, exc_type) for exc_type in config.retryable_exceptions)
        
        # Default retryable exceptions
        retryable_types = (
            ConnectionError,
            TimeoutError,
            OSError,
            IOError,
            CVAutomationException
        )
        
        return isinstance(error, retryable_types)
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt"""
        if config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (2 ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * attempt
        elif config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(config.base_delay, config.base_delay * 2)
        else:
            delay = config.base_delay
        
        # Apply jitter
        if config.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor
        
        # Cap at max delay
        return min(delay, config.max_delay)
    
    def _record_error(self, error_context: ErrorContext):
        """Record error for tracking"""
        self.error_history.append(error_context)
        self.recovery_stats['total_errors'] += 1
        
        # Call error callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_context)
            except Exception as e:
                self._log(f"Error callback failed: {str(e)}", "ERROR")
    
    def add_fallback(self, operation_name: str, fallback_func: Callable):
        """Add fallback function for operation"""
        self.fallback_functions[operation_name] = fallback_func
        self._log(f"Added fallback for {operation_name}")
    
    def remove_fallback(self, operation_name: str):
        """Remove fallback function"""
        if operation_name in self.fallback_functions:
            del self.fallback_functions[operation_name]
            self._log(f"Removed fallback for {operation_name}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error recovery statistics"""
        total_errors = self.recovery_stats['total_errors']
        recovered_errors = self.recovery_stats['recovered_errors']
        
        return {
            'total_errors': total_errors,
            'recovered_errors': recovered_errors,
            'failed_recoveries': self.recovery_stats['failed_recoveries'],
            'recovery_rate': recovered_errors / total_errors if total_errors > 0 else 0,
            'circuit_breaker_trips': self.recovery_stats['circuit_breaker_trips'],
            'active_circuit_breakers': len(self.circuit_breakers),
            'circuit_breaker_states': {
                name: breaker.state.value 
                for name, breaker in self.circuit_breakers.items()
            },
            'fallback_functions': list(self.fallback_functions.keys()),
            'recent_errors': len([e for e in self.error_history 
                                if e.timestamp > datetime.now() - timedelta(hours=1)])
        }
    
    def get_error_history(self, hours: int = 24) -> List[ErrorContext]:
        """Get error history for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [e for e in self.error_history if e.timestamp >= cutoff_time]
    
    def reset_circuit_breaker(self, operation_name: str):
        """Manually reset circuit breaker"""
        if operation_name in self.circuit_breakers:
            breaker = self.circuit_breakers[operation_name]
            breaker.state = CircuitState.CLOSED
            breaker.failure_count = 0
            breaker.success_count = 0
            self._log(f"Reset circuit breaker for {operation_name}")
    
    def reset_all_circuit_breakers(self):
        """Reset all circuit breakers"""
        for operation_name in self.circuit_breakers:
            self.reset_circuit_breaker(operation_name)
    
    def add_error_callback(self, callback: Callable[[ErrorContext], Any]):
        """Add error callback"""
        self.error_callbacks.append(callback)
    
    def add_recovery_callback(self, callback: Callable[[ErrorContext], Any]):
        """Add recovery callback"""
        self.recovery_callbacks.append(callback)
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [ErrorRecovery] {message}")
