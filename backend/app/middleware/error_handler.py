"""Global error handling middleware."""

import logging
import traceback
import uuid
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    return str(uuid.uuid4())


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.
    
    Args:
        request: FastAPI request object
        exc: Application exception
        
    Returns:
        JSON response with error details
    """
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Log the error
    logger.warning(
        f"Application error: {exc.message} "
        f"[request_id={request_id}, status={exc.status_code}]"
    )
    
    # Build error response
    error_response = {
        "error": exc.message,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    # Add details if present
    if exc.details:
        error_response["details"] = exc.details
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def validation_exception_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
        
    Returns:
        JSON response with validation errors
    """
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Format validation errors
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        if field not in errors:
            errors[field] = []
        errors[field].append(error["msg"])
    
    # Log validation error
    logger.info(
        f"Validation error: {len(errors)} field(s) "
        f"[request_id={request_id}]"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "details": {"errors": errors},
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.
    
    Args:
        request: FastAPI request object
        exc: Any exception
        
    Returns:
        JSON response with generic error message
    """
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Log the full error with traceback
    logger.error(
        f"Unexpected error: {str(exc)} "
        f"[request_id={request_id}]\n"
        f"{traceback.format_exc()}"
    )
    
    # In production, don't expose internal error details
    from app.core.config import settings
    
    if settings.is_production:
        error_message = "An internal error occurred"
        error_details = {}
    else:
        error_message = f"Internal server error: {str(exc)}"
        error_details = {
            "type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n"),
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": error_message,
            "details": error_details,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
