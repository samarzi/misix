"""Unit tests for security utilities."""

import pytest
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPass123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPass123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPass123!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPass123!", hashed) is False


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_valid_password(self):
        """Test valid password."""
        is_valid, error = validate_password_strength("StrongPass123!")
        assert is_valid is True
        assert error is None
    
    def test_too_short(self):
        """Test password too short."""
        is_valid, error = validate_password_strength("Short1!")
        assert is_valid is False
        assert "at least 8 characters" in error
    
    def test_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, error = validate_password_strength("lowercase123!")
        assert is_valid is False
        assert "uppercase" in error
    
    def test_no_lowercase(self):
        """Test password without lowercase."""
        is_valid, error = validate_password_strength("UPPERCASE123!")
        assert is_valid is False
        assert "lowercase" in error
    
    def test_no_digit(self):
        """Test password without digit."""
        is_valid, error = validate_password_strength("NoDigits!")
        assert is_valid is False
        assert "digit" in error
    
    def test_no_special_char(self):
        """Test password without special character."""
        is_valid, error = validate_password_strength("NoSpecial123")
        assert is_valid is False
        assert "special character" in error


class TestJWTTokens:
    """Test JWT token functions."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """Test token verification with valid token."""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        
        verified_user_id = verify_token(token, token_type="access")
        assert verified_user_id == user_id
    
    def test_verify_invalid_token(self):
        """Test token verification with invalid token."""
        verified_user_id = verify_token("invalid-token", token_type="access")
        assert verified_user_id is None
    
    def test_verify_wrong_token_type(self):
        """Test token verification with wrong token type."""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        
        # Try to verify as refresh token
        verified_user_id = verify_token(token, token_type="refresh")
        assert verified_user_id is None
