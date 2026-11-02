# Quick Start Guide

Get the AI Agent Integration Hub up and running in minutes.

## Prerequisites

- Python 3.10+
- Redis (for message queuing)
- PostgreSQL (optional, SQLite by default)

## Installation

### 1. Clone and Setup

```bash
cd agent_integration_hub
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Required
GEMINI_API_KEY=your_Gemini_key_here
OPERATOR_USERNAME=operator
OPERATOR_PASSWORD_HASH=paste-the-hash-generated-by-the-password-tool
SESSION_SECRET_KEY=replace-with-a-unique-random-secret-at-least-32-bytes

# Optional (for integrations)
SLACK_BOT_TOKEN=xoxb-your-token
DISCORD_BOT_TOKEN=your-discord-token
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Start Redis

**macOS/Linux:**
```bash
redis-server
```

**Windows (Docker):**
```bash
docker run -d -p 6379:6379 redis:alpine
```

### 4. Initialize Database

```bash
python -c "from backend.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. Start API Server

```bash
uvicorn backend.api.main:app --reload --port 8000
```

### 6. Start the Event Worker

In a second backend terminal:

```bash
python -m backend.worker
```

### 7. Start Frontend (Optional)

In another terminal:

```bash
cd frontend-nextjs
npm ci
npm run dev
```

## Usage

### API Usage

#### Send a Message to Agent

```python
import os
import requests

session = requests.Session()
session.post("http://localhost:8000/api/v1/auth/login", json={
    "username": os.environ["OPERATOR_USERNAME"],
    "password": os.environ["OPERATOR_LOGIN_PASSWORD"],
}).raise_for_status()
csrf = session.cookies["hub_csrf"]
response = session.post("http://localhost:8000/api/v1/agents/chat", json={
    "message": "Hello, how are you?", "channel": "api", "user_id": "user123"
}, headers={"X-CSRF-Token": csrf})
print(response.json())
```

#### Get Message History

```python
messages = session.get("http://localhost:8000/api/v1/messages?limit=10")
print(messages.json())
```

### WebSocket Usage

The dashboard WebSocket uses the signed operator session cookie and validates the request origin. In production, enable secure cookies and connect over `wss://`.

### Integration Setup

#### Slack Integration

1. Create a Slack app at https://api.slack.com/apps
2. Add bot token to `.env`:
   ```
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_SIGNING_SECRET=your-signing-secret
   ```
3. Configure event subscriptions:
   - Request URL: `http://your-domain:8000/api/v1/webhooks/slack`
   - Subscribe to: `message.channels`
4. Install app to workspace

#### Discord Integration

1. Create Discord application at https://discord.com/developers/applications
2. Add bot token to `.env`:
   ```
   DISCORD_BOT_TOKEN=your-discord-token
   ```
3. Invite bot to server with appropriate permissions
4. Configure webhook endpoint (if using webhooks)

#### Email Integration

1. Configure SMTP settings in `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   ```
2. For Gmail, use an App Password (not your regular password)

## Testing

### Health Check

```bash
curl http://localhost:8000/health
```

### Test API Endpoint

Use the authenticated `requests.Session` example above after setting the operator environment values.

## Troubleshooting

### Redis Connection Error

Make sure Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Database Error

Initialize the database:
```bash
python -c "from backend.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Operator sign-in error

Make sure `OPERATOR_USERNAME`, a valid `OPERATOR_PASSWORD_HASH`, and `SESSION_SECRET_KEY` are set in `.env`. Generate the hash with `python -m backend.security.passwords`.

### Integration Not Working

1. Check integration credentials in `.env`
2. Verify integration configuration
3. Check API logs for errors
4. Test integration separately (e.g., test Slack bot token)

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [README.md](README.md) for full documentation
- Explore API docs at http://localhost:8000/docs
- Set up production deployment


