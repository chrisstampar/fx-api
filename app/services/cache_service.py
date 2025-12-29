"""
Caching service for API responses.

Provides in-memory caching with TTL support for read operations.
Can be extended to use Redis if available.
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict
from functools import wraps
from app.config import settings

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except Exception:
    pass


class CacheEntry:
    """Cache entry with TTL."""
    
    def __init__(self, value: Any, ttl: int = 300):
        """
        Initialize cache entry.
        
        Args:
            value: Cached value
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl
    
    def get(self) -> Optional[Any]:
        """Get cached value if not expired."""
        if self.is_expired():
            return None
        return self.value


class CacheService:
    """
    In-memory caching service.
    
    Provides TTL-based caching for API responses.
    Can be extended to use Redis if REDIS_URL is configured.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache service.
        
        Args:
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a hash of the arguments
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        
        value = entry.get()
        if value is None:
            # Entry expired, remove it
            self._cache.pop(key, None)
            self._misses += 1
            return None
        
        self._hits += 1
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            self._cache.pop(key, None)
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }


# Global cache instance
_cache_service = CacheService(default_ttl=settings.REDIS_TTL)


def cached(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Example:
        @cached(ttl=60, key_prefix="balances")
        def get_balance(address: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache_service._generate_key(
                f"{key_prefix}:{func.__name__}",
                *args,
                **kwargs
            )
            
            # Try to get from cache
            cached_value = _cache_service.get(cache_key)
            if cached_value is not None:
                if logger:
                    logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Cache miss, call function
            if logger:
                logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            _cache_service.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache_service._generate_key(
                f"{key_prefix}:{func.__name__}",
                *args,
                **kwargs
            )
            
            # Try to get from cache
            cached_value = _cache_service.get(cache_key)
            if cached_value is not None:
                if logger:
                    logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Cache miss, call function
            if logger:
                logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            _cache_service.set(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    return _cache_service

