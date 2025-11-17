"""Request logging middleware."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests with timing and correlation IDs."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request with logging.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user ID from request if authenticated
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        
        # Log request start
        start_time = time.time()
        
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log error
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(exc)}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )
            raise
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log request completion
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        
        logger.log(
            log_level,
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": duration_ms,
                "status_code": response.status_code,
            },
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
