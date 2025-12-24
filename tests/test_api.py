"""Tests for API endpoints."""

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_chat_without_auth():
    """Test chat endpoint without authentication."""
    response = client.post(
        "/api/v1/agents/chat",
        json={"message": "test", "channel": "api"}
    )
    assert response.status_code == 401


def test_chat_with_auth():
    """Test chat endpoint with authentication."""
    # This test requires proper API key setup
    # Skipping for now as it requires environment setup
    pass

