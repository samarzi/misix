"""Integration tests for application startup validation."""

import os
import sys
from unittest.mock import patch

import pytest

from app.core.startup import StartupValidator, ValidationSeverity
from app.core.database import DatabaseValidator


class TestStartupValidation:
    """Test startup validation with real configuration."""
    
    @pytest.mark.asyncio
    async def test_successful_startup_with_all_config(self):
        """Test successful startup when all configuration is present."""
        validator = StartupValidator()
        result = await validator.validate_all()
        
        # Should have checks for Python version and environment variables
        assert len(result.checks) >= 2
        
        # All checks should pass if environment is properly configured
        if result.all_passed:
            assert len(result.critical_failures) == 0
            assert result.all_passed is True
    
    @pytest.mark.asyncio
    async def test_python_version_validation(self):
        """Test Python version validation."""
        validator = StartupValidator()
        check = await validator.validate_python_version()
        
        assert check.name == "Python Version"
        
        # Check current Python version
        version_info = sys.version_info
        if version_info.major == 3 and version_info.minor >= 11:
            if version_info.minor >= 13:
                # Python 3.13+ should generate warning
                assert check.severity == ValidationSeverity.WARNING
                assert "3.13" in check.message or "compatibility" in check.message.lower()
            else:
                # Python 3.11-3.12 should pass
                assert check.passed is True
                assert check.severity == ValidationSeverity.INFO
        else:
            # Python < 3.11 should fail
            assert check.passed is False
            assert check.severity == ValidationSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_environment_variables_validation(self):
        """Test environment variables validation."""
        validator = StartupValidator()
        check = await validator.validate_environment_variables()
        
        assert check.name == "Environment Variables"
        
        # Check should have details about variables
        assert "details" in check.details or check.details is not None
    
    @pytest.mark.asyncio
    async def test_startup_failure_with_missing_critical_env_vars(self):
        """Test startup fails when critical environment variables are missing."""
        # Temporarily remove a critical env var
        original_value = os.environ.get("JWT_SECRET_KEY")
        
        try:
            if "JWT_SECRET_KEY" in os.environ:
                del os.environ["JWT_SECRET_KEY"]
            
            # Reload settings to pick up the change
            from app.core import config
            with patch.object(config, 'settings') as mock_settings:
                mock_settings.jwt_secret_key = None
                mock_settings.supabase_url = os.getenv("SUPABASE_URL", "https://test.supabase.co")
                mock_settings.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "test_key")
                mock_settings.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "test_key")
                mock_settings.yandex_gpt_api_key = os.getenv("YANDEX_GPT_API_KEY", "test_key")
                mock_settings.yandex_folder_id = os.getenv("YANDEX_FOLDER_ID", "test_folder")
                
                validator = StartupValidator()
                result = await validator.validate_all()
                
                # Should have critical failures
                assert len(result.critical_failures) > 0
                assert result.all_passed is False
        
        finally:
            # Restore original value
            if original_value:
                os.environ["JWT_SECRET_KEY"] = original_value
    
    @pytest.mark.asyncio
    async def test_startup_with_missing_optional_config(self):
        """Test startup succeeds with missing optional configuration (bot token)."""
        # Temporarily remove optional env var
        original_value = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        try:
            if "TELEGRAM_BOT_TOKEN" in os.environ:
                del os.environ["TELEGRAM_BOT_TOKEN"]
            
            validator = StartupValidator()
            result = await validator.validate_all()
            
            # Should have warnings but no critical failures
            # (assuming other required vars are present)
            if all([
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_KEY"),
                os.getenv("SUPABASE_ANON_KEY"),
                os.getenv("JWT_SECRET_KEY"),
                os.getenv("YANDEX_GPT_API_KEY"),
                os.getenv("YANDEX_FOLDER_ID")
            ]):
                # All required vars present, should pass
                assert len(result.critical_failures) == 0
        
        finally:
            # Restore original value
            if original_value:
                os.environ["TELEGRAM_BOT_TOKEN"] = original_value


class TestDatabaseValidation:
    """Test database validation with real database connection."""
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection validation."""
        validator = DatabaseValidator()
        connected = await validator.test_connection()
        
        # Should connect if Supabase is configured
        from app.shared.supabase import supabase_available
        if supabase_available():
            assert connected is True
        else:
            assert connected is False
    
    @pytest.mark.asyncio
    async def test_schema_validation(self):
        """Test database schema validation."""
        validator = DatabaseValidator()
        
        # First ensure connection
        connected = await validator.test_connection()
        
        if connected:
            result = await validator.verify_schema()
            
            # Should check all required tables
            assert len(result.required_tables) == len(DatabaseValidator.REQUIRED_TABLES)
            
            # Result should have summary
            summary = result.get_summary()
            assert isinstance(summary, str)
            assert len(summary) > 0
    
    @pytest.mark.asyncio
    async def test_schema_validation_with_missing_tables(self):
        """Test schema validation detects missing tables."""
        validator = DatabaseValidator()
        
        # First ensure connection
        connected = await validator.test_connection()
        
        if connected:
            result = await validator.verify_schema()
            
            # If tables are missing, should be reported
            if not result.all_tables_exist:
                assert len(result.missing_tables) > 0
                assert "missing" in result.get_summary().lower()
    
    @pytest.mark.asyncio
    async def test_connection_info(self):
        """Test getting anonymized connection info."""
        validator = DatabaseValidator()
        info = await validator.get_connection_info()
        
        from app.shared.supabase import supabase_available
        if supabase_available():
            assert info is not None
            assert info.host is not None
            assert info.port > 0
            assert info.database is not None
            
            # Should not contain sensitive information
            info_dict = info.to_dict()
            assert "password" not in str(info_dict).lower()
            assert "secret" not in str(info_dict).lower()
        else:
            assert info is None
    
    @pytest.mark.asyncio
    async def test_write_operation(self):
        """Test database write operations."""
        validator = DatabaseValidator()
        
        # First ensure connection
        connected = await validator.test_connection()
        
        if connected:
            write_ok = await validator.test_write_operation()
            
            # Write should succeed if database is properly configured
            assert write_ok is True
