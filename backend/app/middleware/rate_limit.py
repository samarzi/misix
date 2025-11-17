"""Rate limiting middleware for API endpoints."""

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)


# ============================================================================
# In-Memory Rate Limiter (Simple Implementation)
# ============================================================================

class InMemoryRateLimiter:
    """Simple in-memory rate limiter using sliding window.
    
    Note: This is a basic implementation suitable for single-instance deployments.
    For production with multiple instances, use Redis-based rate limiting.
    """
    
    def __init__(self):
        # Store: {key: [(timestamp, count), ...]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._cleanup_interval = 60  # Cleanup old entries every 60 seconds
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self, current_time: float, window_seconds: int):
        """Remove entries older than the window."""
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - window_seconds
        for key in list(self._requests.keys()):
            self._requests[key] = [
                (ts, count) for ts, count in self._requests[key]
                if ts > cutoff_time
            ]
            if not self._requests[key]:
                del self._requests[key]
        
        self._last_cleanup = current_time

    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """Check if request is allowed under rate limit.
        
        Args:
            key: Unique identifier for the client (e.g., IP address)
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Cleanup old entries periodically
        self._cleanup_old_entries(current_time, window_seconds)
        
        # Get requests in current window
        requests_in_window = [
            (ts, count) for ts, count in self._requests[key]
            if ts > cutoff_time
        ]
        
        # Count total requests
        total_requests = sum(count for _, count in requests_in_window)
        
        if total_requests >= max_requests:
            # Calculate retry after time
            if requests_in_window:
                oldest_request_time = requests_in_window[0][0]
                retry_after = int(window_seconds - (current_time - oldest_request_time)) + 1
            else:
                retry_after = window_seconds
            
            return False, retry_after
        
        # Add current request
        self._requests[key].append((current_time, 1))
        
        return True, 0


# Global rate limiter instance
_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


# ============================================================================
# Rate Limiting Middleware
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on API endpoints."""
    
    def __init__(self, app, rate_limiter: InMemoryRateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_rate_limiter()
        self.enabled = settings.rate_limit_enabled
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client.
        
        Uses X-Forwarded-For header if behind proxy, otherwise client IP.
        """
        # Check for X-Forwarded-For header (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # Use direct client IP
            client_ip = request.client.host if request.client else "unknown"
        
        return client_ip
    
    def _get_rate_limit_config(self, path: str) -> tuple[int, int]:
        """Get rate limit configuration for the given path.
        
        Returns:
            Tuple of (max_requests, window_seconds)
        """
        # Stricter limits for auth endpoints
        if "/auth/" in path:
            return settings.rate_limit_auth_per_minute, 60
        
        # Default limits for other endpoints
        return settings.rate_limit_per_minute, 60
    
    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if rate limiting should be skipped for this path."""
        # Skip rate limiting for health check and docs
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request with rate limiting."""
        # Skip if rate limiting is disabled
        if not self.enabled:
            return await call_next(request)
        
        path = request.url.path
        
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(path):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Get rate limit config for this path
        max_requests, window_seconds = self._get_rate_limit_config(path)
        
        # Check rate limit
        is_allowed, retry_after = self.rate_limiter.is_allowed(
            key=f"rate_limit:{client_id}:{path}",
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}. "
                f"Retry after {retry_after} seconds."
            )
            
            # Return 429 Too Many Requests
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "details": {
                        "retry_after": retry_after,
                        "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        # Note: Calculating remaining would require another lookup, skipping for performance
        
        return response
