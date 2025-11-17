"""Integration tests for authentication API."""

import pytest


class TestAuthRegistration:
    """Test user registration endpoint."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v2/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/api/v2/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",
                "full_name": "User",
            },
        )
        
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v2/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123!",
                "full_name": "User",
            },
        )
        
        assert response.status_code == 422


class TestAuthLogin:
    """Test user login endpoint."""
    
    def test_login_success(self, client, test_user_data):
        """Test successful login."""
        # Register first
        client.post("/api/v2/auth/register", json=test_user_data)
        
        # Login
        response = client.post(
            "/api/v2/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
    def test_login_wrong_password(self, client, test_user_data):
        """Test login with wrong password."""
        # Register first
        client.post("/api/v2/auth/register", json=test_user_data)
        
        # Login with wrong password
        response = client.post(
            "/api/v2/auth/login",
            json={
                "email": test_user_data["email"],
                "password": "WrongPassword123!",
            },
        )
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v2/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!",
            },
        )
        
        assert response.status_code == 401


class TestAuthProtectedEndpoints:
    """Test protected endpoints."""
    
    def test_get_profile_authenticated(self, client, auth_headers):
        """Test getting profile with valid token."""
        response = client.get("/api/v2/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data
    
    def test_get_profile_unauthenticated(self, client):
        """Test getting profile without token."""
        response = client.get("/api/v2/auth/me")
        
        assert response.status_code == 401
    
    def test_get_profile_invalid_token(self, client):
        """Test getting profile with invalid token."""
        response = client.get(
            "/api/v2/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        
        assert response.status_code == 401
