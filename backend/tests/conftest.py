"""Pytest configuration and fixtures."""

import pytest
from typing import Generator
from fastapi.testclient import TestClient

from app.web.main import create_app


@pytest.fixture(scope="session")
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture(scope="function")
def client(app) -> Generator:
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    }


@pytest.fixture
def auth_headers(client, test_user_data):
    """Get authentication headers with valid token."""
    # Register user
    client.post("/api/v2/auth/register", json=test_user_data)
    
    # Login
    response = client.post(
        "/api/v2/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    
    tokens = response.json()["tokens"]
    access_token = tokens["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}
