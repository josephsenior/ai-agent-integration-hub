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
API_SECRET_KEY=your-secret-key-here

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

### 6. Start Frontend (Optional)

In another terminal:

```bash
streamlit run frontend/app.py
```

## Usage

### API Usage

#### Send a Message to Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "channel": "api",
    "user_id": "user123"
  }'
```

#### Get Message History

```bash
curl -X GET "http://localhost:8000/api/v1/messages?limit=10" \
  -H "Authorization: Bearer your-secret-key"
```

### WebSocket Usage

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: "message",
        message: "Hello from WebSocket!",
        context: {}
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Response:', data);
};
```

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

```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message", "channel": "api"}'
```

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

### API Key Error

Make sure `API_SECRET_KEY` in `.env` matches the Bearer token in your requests.

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


