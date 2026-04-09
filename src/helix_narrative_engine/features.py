"""
Advanced features module for helix-narrative-engine.

Provides caching, monitoring, resilience patterns, and optimization utilities.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Caching System
# ============================================================================

@dataclass
class CacheEntry:
    """Represents a cached value with metadata."""
    value: Any
    created_at: datetime
    ttl: int  # Time to live in seconds
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl == -1:  # Never expires
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def update_access(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class CacheManager:
    """Intelligent caching system with multiple eviction policies."""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 3600,
        eviction_policy: str = "lru"
    ):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of cached items
            ttl: Default time-to-live in seconds (-1 for never expire)
            eviction_policy: "lru", "lfu", or "fifo"
        """
        self.max_size = max_size
        self.ttl = ttl
        self.eviction_policy = eviction_policy
        self.cache: Dict[str, CacheEntry] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_accesses": 0
        }
    
    def _generate_key(self, namespace: str, data: Any) -> str:
        """Generate cache key from namespace and data."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{namespace}:{hash_obj.hexdigest()}"
    
    def get(self, namespace: str, key_data: Any) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            namespace: Cache namespace
            key_data: Data to generate cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(namespace, key_data)
        self.stats["total_accesses"] += 1
        
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            self.stats["misses"] += 1
            return None
        
        entry.update_access()
        self.stats["hits"] += 1
        
        # Move to end (for LRU)
        if self.eviction_policy == "lru":
            self.cache.move_to_end(key)
        
        return entry.value
    
    def set(
        self,
        namespace: str,
        key_data: Any,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Store value in cache.
        
        Args:
            namespace: Cache namespace
            key_data: Data to generate cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        key = self._generate_key(namespace, key_data)
        ttl = ttl or self.ttl
        
        # Evict if necessary
        if len(self.cache) >= self.max_size:
            self._evict()
        
        self.cache[key] = CacheEntry(
            value=value,
            created_at=datetime.now(),
            ttl=ttl
        )
        
        # Move to end (for LRU)
        if self.eviction_policy == "lru":
            self.cache.move_to_end(key)
    
    def _evict(self) -> None:
        """Evict item based on policy."""
        if not self.cache:
            return
        
        self.stats["evictions"] += 1
        
        if self.eviction_policy == "lru":
            # Remove least recently used (first item)
            self.cache.popitem(last=False)
        elif self.eviction_policy == "lfu":
            # Remove least frequently used
            key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
            del self.cache[key]
        elif self.eviction_policy == "fifo":
            # Remove first inserted (first item)
            self.cache.popitem(last=False)
    
    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            **self.stats,
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "eviction_policy": self.eviction_policy
        }


# ============================================================================
# Monitoring System
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tokens_used: int = 0
    cost: float = 0.0
    quality_score: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def finalize(self) -> None:
        """Finalize metrics after operation completion."""
        if self.end_time is None:
            self.end_time = time.time()
        self.duration = self.end_time - self.start_time


class MonitoringSystem:
    """System for monitoring and collecting performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialize monitoring system.
        
        Args:
            max_metrics: Maximum metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self.metrics: List[PerformanceMetrics] = []
        self.lock = asyncio.Lock()
    
    async def record_metric(self, metric: PerformanceMetrics) -> None:
        """Record a performance metric."""
        async with self.lock:
            metric.finalize()
            self.metrics.append(metric)
            
            # Keep only recent metrics
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregated statistics.
        
        Args:
            operation: Filter by operation name (None for all)
            
        Returns:
            Aggregated statistics
        """
        metrics = self.metrics
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        if not metrics:
            return {"count": 0}
        
        durations = [m.duration for m in metrics if m.duration]
        costs = [m.cost for m in metrics]
        quality_scores = [m.quality_score for m in metrics if m.quality_score > 0]
        
        return {
            "count": len(metrics),
            "success_count": sum(1 for m in metrics if m.success),
            "error_count": sum(1 for m in metrics if not m.success),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "total_cost": sum(costs),
            "avg_cost": sum(costs) / len(costs) if costs else 0,
            "avg_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "total_tokens": sum(m.tokens_used for m in metrics)
        }


# ============================================================================
# Resilience Patterns
# ============================================================================

class RetryPolicy:
    """Retry policy with exponential backoff."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry policy.
        
        Args:
            max_attempts: Maximum retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry policy.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = self.get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
        
        raise last_exception


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Time before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception if circuit is open
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has passed."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: float, burst: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            rate: Tokens per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            Wait time in seconds
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            wait_time = (tokens - self.tokens) / self.rate
            self.tokens = 0
            return wait_time


# ============================================================================
# Health Check System
# ============================================================================

@dataclass
class HealthStatus:
    """Health status information."""
    healthy: bool
    timestamp: datetime
    checks: Dict[str, bool]
    details: Dict[str, str] = field(default_factory=dict)


class HealthChecker:
    """System health checking."""
    
    def __init__(self):
        """Initialize health checker."""
        self.checks: Dict[str, Callable] = {}
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check.
        
        Args:
            name: Check name
            check_func: Async function that returns bool
        """
        self.checks[name] = check_func
    
    async def check_health(self) -> HealthStatus:
        """
        Run all health checks.
        
        Returns:
            Health status
        """
        results = {}
        details = {}
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = result
                details[name] = "OK" if result else "FAILED"
            except Exception as e:
                results[name] = False
                details[name] = str(e)
        
        healthy = all(results.values()) if results else True
        
        return HealthStatus(
            healthy=healthy,
            timestamp=datetime.now(),
            checks=results,
            details=details
        )


# ============================================================================
# Utility Functions
# ============================================================================

async def with_timeout(
    coro,
    timeout: float
) -> Any:
    """
    Execute coroutine with timeout.
    
    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        
    Returns:
        Coroutine result
        
    Raises:
        asyncio.TimeoutError if timeout exceeded
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {timeout}s")
        raise


def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"{func.__name__} took {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper
