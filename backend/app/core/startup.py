"""Startup validation for MISIX application.

This module validates system requirements and configuration before the application starts.
It ensures all required environment variables are present, Python version is compatible,
and critical services are accessible.
"""

import sys
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity level for validation checks."""
    
    CRITICAL = "critical"  # Must pass for app to start
    WARNING = "warning"    # Should pass but app can continue
    INFO = "info"          # Informational only


@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    
    name: str
    severity: ValidationSeverity
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    exception: Optional[Exception] = None
    
    def __str__(self) -> str:
        """String representation of validation check."""
        status = "✅" if self.passed else "❌"
        return f"{status} {self.name}: {self.message}"


@dataclass
class StartupValidationResult:
    """Aggregated results of all startup validations."""
    
    checks: list[ValidationCheck] = field(default_factory=list)
    
    @property
    def all_passed(self) -> bool:
        """Check if all validations passed."""
        return all(check.passed for check in self.checks)
    
    @property
    def critical_failures(self) -> list[ValidationCheck]:
        """Get all critical failures."""
        return [
            check for check in self.checks
            if not check.passed and check.severity == ValidationSeverity.CRITICAL
        ]
    
    @property
    def warnings(self) -> list[ValidationCheck]:
        """Get all warnings."""
        return [
            check for check in self.checks
            if not check.passed and check.severity == ValidationSeverity.WARNING
        ]
    
    @property
    def info_messages(self) -> list[ValidationCheck]:
        """Get all info messages."""
        return [
            check for check in self.checks
            if check.severity == ValidationSeverity.INFO
        ]


class StartupValidator:
    """Validates system requirements and configuration on startup."""
    
    def __init__(self):
        """Initialize startup validator."""
        self.result = StartupValidationResult()
    
    async def validate_all(self) -> StartupValidationResult:
        """Run all validation checks.
        
        Returns:
            StartupValidationResult with all check results
        """
        logger.info("🔍 Running startup validation checks...")
        
        # Run all validation checks
        await self.validate_python_version()
        await self.validate_environment_variables()
        
        # Log summary
        if self.result.all_passed:
            logger.info(f"✅ All {len(self.result.checks)} validation checks passed")
        else:
            critical_count = len(self.result.critical_failures)
            warning_count = len(self.result.warnings)
            if critical_count > 0:
                logger.error(f"❌ {critical_count} critical validation failures")
            if warning_count > 0:
                logger.warning(f"⚠️  {warning_count} validation warnings")
        
        return self.result
    
    async def validate_python_version(self) -> ValidationCheck:
        """Verify Python version compatibility.
        
        Returns:
            ValidationCheck result
        """
        version_info = sys.version_info
        version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        
        # Check for Python 3.11+
        if version_info.major == 3 and version_info.minor >= 11:
            # Warn about Python 3.13
            if version_info.minor >= 13:
                check = ValidationCheck(
                    name="Python Version",
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=f"Python {version_str} detected. Python 3.13+ has known compatibility issues with python-telegram-bot. Recommend Python 3.11.",
                    details={
                        "version": version_str,
                        "major": version_info.major,
                        "minor": version_info.minor,
                        "micro": version_info.micro,
                        "recommended": "3.11"
                    }
                )
            else:
                check = ValidationCheck(
                    name="Python Version",
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    message=f"Python {version_str} - compatible",
                    details={
                        "version": version_str,
                        "major": version_info.major,
                        "minor": version_info.minor,
                        "micro": version_info.micro
                    }
                )
        else:
            check = ValidationCheck(
                name="Python Version",
                severity=ValidationSeverity.CRITICAL,
                passed=False,
                message=f"Python {version_str} is not supported. Requires Python 3.11+",
                details={
                    "version": version_str,
                    "required": "3.11+",
                    "major": version_info.major,
                    "minor": version_info.minor
                }
            )
        
        self.result.checks.append(check)
        return check
    
    async def validate_environment_variables(self) -> ValidationCheck:
        """Verify all required environment variables are present.
        
        Returns:
            ValidationCheck result
        """
        required_vars = {
            "SUPABASE_URL": settings.supabase_url,
            "SUPABASE_SERVICE_KEY": settings.supabase_service_key,
            "SUPABASE_ANON_KEY": settings.supabase_anon_key,
            "JWT_SECRET_KEY": settings.jwt_secret_key,
            "YANDEX_GPT_API_KEY": settings.yandex_gpt_api_key,
            "YANDEX_FOLDER_ID": settings.yandex_folder_id,
        }
        
        optional_vars = {
            "TELEGRAM_BOT_TOKEN": settings.telegram_bot_token,
            "DATABASE_URL": getattr(settings, "database_url", None),
            "REDIS_URL": settings.redis_url,
        }
        
        missing_required = []
        missing_optional = []
        
        # Check required variables
        for var_name, var_value in required_vars.items():
            if not var_value or (isinstance(var_value, str) and not var_value.strip()):
                missing_required.append(var_name)
        
        # Check optional variables
        for var_name, var_value in optional_vars.items():
            if not var_value or (isinstance(var_value, str) and not var_value.strip()):
                missing_optional.append(var_name)
        
        # Create validation check
        if missing_required:
            check = ValidationCheck(
                name="Environment Variables",
                severity=ValidationSeverity.CRITICAL,
                passed=False,
                message=f"Missing required environment variables: {', '.join(missing_required)}",
                details={
                    "missing_required": missing_required,
                    "missing_optional": missing_optional,
                    "total_required": len(required_vars),
                    "total_optional": len(optional_vars)
                }
            )
        elif missing_optional:
            check = ValidationCheck(
                name="Environment Variables",
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"Missing optional environment variables: {', '.join(missing_optional)}. Some features may be disabled.",
                details={
                    "missing_optional": missing_optional,
                    "total_required": len(required_vars),
                    "total_optional": len(optional_vars)
                }
            )
        else:
            check = ValidationCheck(
                name="Environment Variables",
                severity=ValidationSeverity.INFO,
                passed=True,
                message=f"All {len(required_vars)} required and {len(optional_vars)} optional variables present",
                details={
                    "total_required": len(required_vars),
                    "total_optional": len(optional_vars)
                }
            )
        
        self.result.checks.append(check)
        return check
    
    def _sanitize_value(self, value: str, show_length: int = 4) -> str:
        """Sanitize sensitive value for logging.
        
        Args:
            value: Value to sanitize
            show_length: Number of characters to show at start
            
        Returns:
            Sanitized value like "abcd...xyz" (length 10)
        """
        if not value or len(value) <= show_length:
            return "***"
        return f"{value[:show_length]}...{value[-3:]}"
