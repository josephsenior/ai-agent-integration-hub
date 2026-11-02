# Test Suite

Comprehensive test suite for the AI Agent Integration Hub.

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=backend --cov-report=html
```

### Run specific test categories:
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# API tests
pytest -m api

# Agent tests
pytest -m agent

# WebSocket tests
pytest -m websocket

# Integration adapter tests
pytest -m integration_adapter
```

### Run specific test file:
```bash
pytest tests/test_api.py
pytest tests/test_agents.py
pytest tests/test_integrations.py
pytest tests/test_websocket.py
pytest tests/test_models.py
```

### Run with verbose output:
```bash
pytest -v
```

### Run specific test:
```bash
pytest tests/test_api.py::TestChatEndpoint::test_chat_with_auth
```

## Test Structure

```
tests/
├── __init__.py          # Test package initialization
├── conftest.py          # Shared fixtures and configuration
├── test_api.py          # API endpoint tests
├── test_agents.py       # Agent functionality tests
├── test_integrations.py # Integration adapter tests
├── test_websocket.py    # WebSocket functionality tests
└── test_models.py       # Data model tests
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Fast, isolated tests
- Test individual functions/classes
- No external dependencies

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- May use test database/Redis
- Slower than unit tests

### API Tests (`@pytest.mark.api`)
- Test HTTP endpoints
- Use TestClient
- Test authentication, validation, responses

### Agent Tests (`@pytest.mark.agent`)
- Test agent processing logic
- Mock LLM calls
- Test context handling

### WebSocket Tests (`@pytest.mark.websocket`)
- Test WebSocket connections
- Test message broadcasting
- Test real-time communication

### Integration Adapter Tests (`@pytest.mark.integration_adapter`)
- Test Slack, Discord, Email, Webhook adapters
- Test message parsing and sending
- Mock external APIs

## Fixtures

Shared fixtures are defined in `conftest.py`:

- `mock_db_session` - Mock database session
- `override_get_db` - Override database dependency
- `sample_message` - Sample message for testing
- `mock_agent` - Mock agent instance
- `mock_redis_service` - Mock Redis service
- `auth_headers` - Authentication headers
- `slack_payload` - Sample Slack webhook payload
- `discord_payload` - Sample Discord webhook payload
- `email_payload` - Sample email webhook payload

## Coverage Goals

- **Target**: 80%+ code coverage
- **Critical paths**: 100% coverage
  - API endpoints
  - Agent processing
  - Integration adapters
  - Error handling

## Writing New Tests

1. **Follow naming convention**: `test_<functionality>.py`
2. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.api`, etc.
3. **Use fixtures**: Leverage shared fixtures from `conftest.py`
4. **Mock external dependencies**: Don't make real API calls
5. **Test edge cases**: Include error scenarios
6. **Keep tests isolated**: Each test should be independent

## Example Test

```python
@pytest.mark.api
class TestMyEndpoint:
    """Tests for my endpoint."""

    def test_endpoint_success(self, auth_headers, override_get_db):
        """Test successful endpoint call."""
        response = client.get("/api/v1/my-endpoint", headers=auth_headers)
        assert response.status_code == 200
        assert "data" in response.json()

    def test_endpoint_unauthorized(self):
        """Test endpoint without authentication."""
        response = client.get("/api/v1/my-endpoint")
        assert response.status_code == 401
```

## Continuous Integration

Tests should pass in CI/CD pipeline:
- All tests must pass
- Coverage must meet minimum threshold
- No flaky tests

## Troubleshooting

### Tests failing due to imports:
- Ensure you're in the project root directory
- Check that `backend` package is in Python path

### Async test issues:
- Use `@pytest.mark.asyncio` for async tests
- Use `AsyncMock` for mocking async functions

### Database dependency issues:
- Use `override_get_db` fixture to mock database
- Don't use real database in tests
