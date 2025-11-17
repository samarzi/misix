"""Redis caching utilities."""

import json
import logging
from typing import Any, Optional
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client (optional dependency)
_redis_client = None


def get_redis_client():
    """Get Redis client instance.
    
    Returns:
        Redis client or None if not configured
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    if not settings.redis_url:
        logger.info("Redis not configured, caching disabled")
        return None
    
    try:
        import redis
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        # Test connection
        _redis_client.ping()
        logger.info("Redis connection established")
        return _redis_client
    except ImportError:
        logger.warning("Redis package not installed, caching disabled")
        return None
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in cache.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 5 minutes)
        
    Returns:
        True if successful
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        serialized = json.dumps(value)
        client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed for key {key}: {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching pattern.
    
    Args:
        pattern: Key pattern (e.g., "user:*")
        
    Returns:
        Number of keys deleted
    """
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache delete pattern failed for {pattern}: {e}")
        return 0


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Example:
        @cached(ttl=600, key_prefix="user")
        async def get_user(user_id: str):
            return await fetch_user(user_id)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                cache_set(cache_key, result, ttl)
                logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


# Predefined cache key builders
def user_cache_key(user_id: str) -> str:
    """Build cache key for user data."""
    return f"user:{user_id}"


def session_cache_key(session_id: str) -> str:
    """Build cache key for session data."""
    return f"session:{session_id}"


def conversation_cache_key(user_id: str) -> str:
    """Build cache key for conversation data."""
    return f"conversation:{user_id}"
