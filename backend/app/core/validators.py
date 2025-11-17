"""Input validation utilities."""

import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError


# ============================================================================
# File Upload Validation
# ============================================================================

# Allowed MIME types for file uploads (whitelist approach)
ALLOWED_MIME_TYPES = {
    # Images
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/gif": [".gif"],
    "image/webp": [".webp"],
    # Documents
    "application/pdf": [".pdf"],
    "text/plain": [".txt"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/vnd.ms-excel": [".xls"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    # Archives
    "application/zip": [".zip"],
    "application/x-rar-compressed": [".rar"],
    # Audio
    "audio/mpeg": [".mp3"],
    "audio/ogg": [".ogg"],
    "audio/wav": [".wav"],
}


def validate_file_extension(filename: str) -> tuple[bool, Optional[str]]:
    """Validate file extension against allowed list.
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_file_extension("document.pdf")
        (True, None)
        >>> validate_file_extension("script.exe")
        (False, "File extension '.exe' is not allowed")
    """
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    
    if not extension:
        return False, "File must have an extension"
    
    allowed_extensions = settings.allowed_upload_extensions
    
    if extension not in allowed_extensions:
        return False, f"File extension '{extension}' is not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    return True, None


def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
    """Validate file size against maximum allowed size.
    
    Args:
        file_size: Size of the file in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_file_size(1024 * 1024)  # 1 MB
        (True, None)
        >>> validate_file_size(100 * 1024 * 1024)  # 100 MB
        (False, "File size exceeds maximum allowed size of 10 MB")
    """
    max_size = settings.max_upload_size_bytes
    
    if file_size > max_size:
        max_size_mb = settings.max_upload_size_mb
        return False, f"File size exceeds maximum allowed size of {max_size_mb} MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None


def validate_mime_type(filename: str, content_type: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """Validate MIME type of the file.
    
    Args:
        filename: Name of the file
        content_type: Content-Type header from upload (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_mime_type("document.pdf", "application/pdf")
        (True, None)
        >>> validate_mime_type("script.exe", "application/x-msdownload")
        (False, "File type 'application/x-msdownload' is not allowed")
    """
    # Get MIME type from filename
    guessed_type, _ = mimetypes.guess_type(filename)
    
    # Use provided content_type or guessed type
    mime_type = content_type or guessed_type
    
    if not mime_type:
        return False, "Could not determine file type"
    
    # Check if MIME type is in allowed list
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, f"File type '{mime_type}' is not allowed"
    
    # Verify extension matches MIME type
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    
    expected_extensions = ALLOWED_MIME_TYPES[mime_type]
    if extension not in expected_extensions:
        return False, f"File extension '{extension}' does not match content type '{mime_type}'"
    
    return True, None


def validate_image_content(file_content: bytes) -> tuple[bool, Optional[str]]:
    """Validate that file content is actually an image.
    
    This checks the file magic bytes to ensure it's a real image file,
    not just a renamed executable.
    
    Args:
        file_content: First few bytes of the file
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> with open("image.jpg", "rb") as f:
        ...     content = f.read(12)
        ...     validate_image_content(content)
        (True, None)
    """
    # Check for common image file signatures (magic bytes)
    image_signatures = {
        b"\xFF\xD8\xFF": "JPEG",
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"GIF87a": "GIF",
        b"GIF89a": "GIF",
        b"RIFF": "WEBP",  # WEBP starts with RIFF
    }
    
    for signature, format_name in image_signatures.items():
        if file_content.startswith(signature):
            return True, None
    
    return False, "File does not appear to be a valid image"


async def validate_upload_file(file: UploadFile) -> None:
    """Validate an uploaded file comprehensively.
    
    This function performs all validation checks on an uploaded file:
    - File extension
    - File size
    - MIME type
    - Content validation (for images)
    
    Args:
        file: FastAPI UploadFile object
        
    Raises:
        ValidationError: If any validation check fails
        
    Example:
        >>> from fastapi import UploadFile
        >>> file = UploadFile(filename="document.pdf")
        >>> await validate_upload_file(file)
    """
    errors = {}
    
    # Validate filename exists
    if not file.filename:
        raise ValidationError(
            message="File upload validation failed",
            errors={"file": ["Filename is required"]},
        )
    
    # Validate file extension
    is_valid, error = validate_file_extension(file.filename)
    if not is_valid:
        errors["extension"] = [error]
    
    # Validate MIME type
    is_valid, error = validate_mime_type(file.filename, file.content_type)
    if not is_valid:
        errors["mime_type"] = [error]
    
    # Read file to check size and content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Reset file pointer for later use
    await file.seek(0)
    
    # Validate file size
    is_valid, error = validate_file_size(file_size)
    if not is_valid:
        errors["size"] = [error]
    
    # Validate image content if it's an image
    if file.content_type and file.content_type.startswith("image/"):
        # Read first 12 bytes for magic number check
        magic_bytes = file_content[:12]
        is_valid, error = validate_image_content(magic_bytes)
        if not is_valid:
            errors["content"] = [error]
    
    # Raise validation error if any checks failed
    if errors:
        raise ValidationError(
            message="File upload validation failed",
            errors=errors,
        )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for storage
        
    Example:
        >>> sanitize_filename("../../etc/passwd")
        'passwd'
        >>> sanitize_filename("my document (1).pdf")
        'my_document_1.pdf'
    """
    # Get just the filename, no path components
    file_path = Path(filename)
    clean_name = file_path.name
    
    # Remove or replace dangerous characters
    # Keep only alphanumeric, dots, hyphens, and underscores
    safe_chars = []
    for char in clean_name:
        if char.isalnum() or char in ".-_":
            safe_chars.append(char)
        elif char == " ":
            safe_chars.append("_")
    
    sanitized = "".join(safe_chars)
    
    # Ensure filename is not empty
    if not sanitized or sanitized == ".":
        sanitized = "unnamed_file"
    
    # Ensure extension is preserved
    if "." not in sanitized:
        extension = file_path.suffix
        if extension:
            sanitized += extension
    
    return sanitized


# ============================================================================
# Text Input Validation
# ============================================================================

def validate_no_html_tags(text: str) -> tuple[bool, Optional[str]]:
    """Validate that text doesn't contain HTML tags.
    
    Args:
        text: Text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_no_html_tags("Hello world")
        (True, None)
        >>> validate_no_html_tags("<script>alert('xss')</script>")
        (False, "HTML tags are not allowed")
    """
    import re
    
    # Simple check for HTML tags
    if re.search(r"<[^>]+>", text):
        return False, "HTML tags are not allowed"
    
    return True, None


def validate_no_sql_injection(text: str) -> tuple[bool, Optional[str]]:
    """Validate that text doesn't contain common SQL injection patterns.
    
    Note: This is a basic check. Always use parameterized queries!
    
    Args:
        text: Text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_no_sql_injection("Hello world")
        (True, None)
        >>> validate_no_sql_injection("'; DROP TABLE users; --")
        (False, "Input contains suspicious patterns")
    """
    import re
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--)",
        r"(;.*--)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
    ]
    
    text_upper = text.upper()
    
    for pattern in sql_patterns:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return False, "Input contains suspicious patterns"
    
    return True, None


def sanitize_text_input(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize text input by removing dangerous characters.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length to truncate to (optional)
        
    Returns:
        Sanitized text
        
    Example:
        >>> sanitize_text_input("<script>alert('xss')</script>")
        "scriptalert('xss')/script"
        >>> sanitize_text_input("Hello world", max_length=5)
        "Hello"
    """
    import html
    
    # HTML escape to prevent XSS
    sanitized = html.escape(text)
    
    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
