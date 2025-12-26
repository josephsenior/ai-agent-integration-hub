"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from backend.api.main import app
from backend.core.config import settings
from backend.core.database import get_db

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
        "/api/v1/agents/chat", json={"message": "test", "channel": "api"}
    )
    assert response.status_code == 401

@pytest.fixture
def mock_db():
    mock = AsyncMock()
    # Mock the execute for list_messages
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock.execute.return_value = mock_result
    
    # Mock commit and refresh
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    return mock

@pytest.fixture
def override_get_db(mock_db):
    async def _get_db():
        yield mock_db
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@patch("backend.api.main.agent")
@patch("backend.api.main.redis_service")
def test_chat_with_auth(mock_redis, mock_agent, override_get_db, mock_db):
    """Test chat endpoint with authentication."""
    # Mock the Agent response
    mock_agent.process = AsyncMock(return_value="This is a mocked response")
    
    # Mock Redis publish
    mock_redis.publish_event = AsyncMock()
    
    # Mock DB operations
    mock_db.add = MagicMock()
    
    # Use the secret key from settings (lowercase)
    headers = {"Authorization": f"Bearer {settings.api_secret_key}"}
    
    response = client.post(
        "/api/v1/agents/chat", 
        json={"message": "hello", "channel": "api", "user_id": "test_user"},
        headers=headers
    )
    
    if response.status_code == 500:
        print(f"Error detail: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "This is a mocked response"
    assert data["status"] == "completed"

def test_get_messages_unauthorized():
    """Test getting messages without auth."""
    response = client.get("/api/v1/messages")
    assert response.status_code == 401

def test_get_messages_authorized(override_get_db, mock_db):
    """Test getting messages with auth."""
    headers = {"Authorization": f"Bearer {settings.api_secret_key}"}
    response = client.get("/api/v1/messages", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
