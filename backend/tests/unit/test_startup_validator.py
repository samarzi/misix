"""Unit tests for startup validator."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from app.core.startup import (
    StartupValidator,
    ValidationCheck,
    ValidationSeverity,
    StartupValidationResult
)


class TestValidationCheck:
    """Test ValidationCheck data model."""
    
    def test_validation_check_creation(self):
        """Test creating a validation check."""
        check = ValidationCheck(
            name="Test Check",
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Test passed"
        )
        
        assert check.name == "Test Check"
        assert check.severity == ValidationSeverity.INFO
        assert check.passed is True
        assert check.message == "Test passed"
        assert check.details == {}
        assert check.exception is None
    
    def test_validation_check_with_details(self):
        """Test validation check with details."""
        details = {"key": "value", "count": 42}
        check = ValidationCheck(
            name="Test",
            severity=ValidationSeverity.CRITICAL,
            passed=False,
            message="Failed",
            details=details
        )
        
        assert check.details == details
    
    def test_validation_check_string_representation(self):
        """Test string representation of validation check."""
        check_passed = ValidationCheck(
            name="Test",
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Success"
        )
        
        check_failed = ValidationCheck(
            name="Test",
            severity=ValidationSeverity.CRITICAL,
            passed=False,
            message="Failed"
        )
        
        assert "✅" in str(check_passed)
        assert "❌" in str(check_failed)
        assert "Test" in str(check_passed)
        assert "Success" in str(check_passed)


class TestStartupValidationResult:
    """Test StartupValidationResult data model."""
    
    def test_empty_result(self):
        """Test empty validation result."""
        result = StartupValidationResult()
        
        assert result.checks == []
        assert result.all_passed is True
        assert result.critical_failures == []
        assert result.warnings == []
    
    def test_all_passed(self):
        """Test result with all checks passed."""
        result = StartupValidationResult(checks=[
            ValidationCheck("Check 1", ValidationSeverity.INFO, True, "OK"),
            ValidationCheck("Check 2", ValidationSeverity.INFO, True, "OK"),
        ])
        
        assert result.all_passed is True
        assert len(result.critical_failures) == 0
        assert len(result.warnings) == 0
    
    def test_critical_failures(self):
        """Test result with critical failures."""
        critical_check = ValidationCheck(
            "Critical", ValidationSeverity.CRITICAL, False, "Failed"
        )
        result = StartupValidationResult(checks=[
            ValidationCheck("Check 1", ValidationSeverity.INFO, True, "OK"),
            critical_check,
        ])
        
        assert result.all_passed is False
        assert len(result.critical_failures) == 1
        assert result.critical_failures[0] == critical_check
    
    def test_warnings(self):
        """Test result with warnings."""
        warning_check = ValidationCheck(
            "Warning", ValidationSeverity.WARNING, False, "Warning"
        )
        result = StartupValidationResult(checks=[
            ValidationCheck("Check 1", ValidationSeverity.INFO, True, "OK"),
            warning_check,
        ])
        
        assert result.all_passed is False
        assert len(result.warnings) == 1
        assert result.warnings[0] == warning_check
        assert len(result.critical_failures) == 0


class TestStartupValidator:
    """Test StartupValidator with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_validate_python_version_compatible(self):
        """Test Python version validation with compatible version."""
        validator = StartupValidator()
        
        with patch.object(sys, 'version_info') as mock_version:
            # Mock Python 3.11
            mock_version.major = 3
            mock_version.minor = 11
            mock_version.micro = 5
            
            check = await validator.validate_python_version()
            
            assert check.name == "Python Version"
            assert check.passed is True
            assert check.severity == ValidationSeverity.INFO
            assert "3.11" in check.message
    
    @pytest.mark.asyncio
    async def test_validate_python_version_warning_313(self):
        """Test Python version validation with Python 3.13."""
        validator = StartupValidator()
        
        with patch.object(sys, 'version_info') as mock_version:
            # Mock Python 3.13
            mock_version.major = 3
            mock_version.minor = 13
            mock_version.micro = 0
            
            check = await validator.validate_python_version()
            
            assert check.name == "Python Version"
            assert check.passed is False
            assert check.severity == ValidationSeverity.WARNING
            assert "3.13" in check.message or "compatibility" in check.message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_python_version_critical_old(self):
        """Test Python version validation with old Python version."""
        validator = StartupValidator()
        
        with patch.object(sys, 'version_info') as mock_version:
            # Mock Python 3.9
            mock_version.major = 3
            mock_version.minor = 9
            mock_version.micro = 0
            
            check = await validator.validate_python_version()
            
            assert check.name == "Python Version"
            assert check.passed is False
            assert check.severity == ValidationSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_validate_environment_variables_all_present(self):
        """Test environment variables validation when all are present."""
        validator = StartupValidator()
        
        # Mock settings with all required variables
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_service_key = "test_service_key"
            mock_settings.supabase_anon_key = "test_anon_key"
            mock_settings.jwt_secret_key = "test_jwt_secret_key_32_chars_long"
            mock_settings.yandex_gpt_api_key = "test_yandex_key"
            mock_settings.yandex_folder_id = "test_folder_id"
            mock_settings.telegram_bot_token = "test_bot_token"
            mock_settings.redis_url = "redis://localhost"
            
            check = await validator.validate_environment_variables()
            
            assert check.name == "Environment Variables"
            assert check.passed is True
            assert check.severity == ValidationSeverity.INFO
    
    @pytest.mark.asyncio
    async def test_validate_environment_variables_missing_required(self):
        """Test environment variables validation with missing required vars."""
        validator = StartupValidator()
        
        # Mock settings with missing required variable
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_service_key = "test_service_key"
            mock_settings.supabase_anon_key = "test_anon_key"
            mock_settings.jwt_secret_key = None  # Missing!
            mock_settings.yandex_gpt_api_key = "test_yandex_key"
            mock_settings.yandex_folder_id = "test_folder_id"
            mock_settings.telegram_bot_token = None
            mock_settings.redis_url = None
            
            check = await validator.validate_environment_variables()
            
            assert check.name == "Environment Variables"
            assert check.passed is False
            assert check.severity == ValidationSeverity.CRITICAL
            assert "JWT_SECRET_KEY" in check.message
    
    @pytest.mark.asyncio
    async def test_validate_environment_variables_missing_optional(self):
        """Test environment variables validation with missing optional vars."""
        validator = StartupValidator()
        
        # Mock settings with all required but missing optional
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_service_key = "test_service_key"
            mock_settings.supabase_anon_key = "test_anon_key"
            mock_settings.jwt_secret_key = "test_jwt_secret_key_32_chars_long"
            mock_settings.yandex_gpt_api_key = "test_yandex_key"
            mock_settings.yandex_folder_id = "test_folder_id"
            mock_settings.telegram_bot_token = None  # Optional
            mock_settings.redis_url = None  # Optional
            
            check = await validator.validate_environment_variables()
            
            assert check.name == "Environment Variables"
            assert check.passed is False
            assert check.severity == ValidationSeverity.WARNING
            assert "optional" in check.message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_all_aggregates_checks(self):
        """Test that validate_all runs all checks and aggregates results."""
        validator = StartupValidator()
        
        with patch('app.core.startup.settings') as mock_settings:
            # Mock all required settings
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_service_key = "test_key"
            mock_settings.supabase_anon_key = "test_key"
            mock_settings.jwt_secret_key = "test_jwt_secret_key_32_chars_long"
            mock_settings.yandex_gpt_api_key = "test_key"
            mock_settings.yandex_folder_id = "test_folder"
            mock_settings.telegram_bot_token = "test_token"
            mock_settings.redis_url = None
            
            result = await validator.validate_all()
            
            # Should have at least 2 checks (Python version + env vars)
            assert len(result.checks) >= 2
            
            # Should have checks for both validators
            check_names = [check.name for check in result.checks]
            assert "Python Version" in check_names
            assert "Environment Variables" in check_names
    
    def test_sanitize_value(self):
        """Test value sanitization for logging."""
        validator = StartupValidator()
        
        # Test with long value
        sanitized = validator._sanitize_value("abcdefghijklmnopqrstuvwxyz", show_length=4)
        assert sanitized == "abcd...xyz"
        assert len(sanitized) == 10
        
        # Test with short value
        sanitized_short = validator._sanitize_value("abc", show_length=4)
        assert sanitized_short == "***"
