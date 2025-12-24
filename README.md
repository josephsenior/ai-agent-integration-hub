# 🔌 AI Agent Integration Hub

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-orange.svg)](https://www.langchain.com/)

Production-ready platform that connects AI agents to external services and communication channels. Provides a unified API gateway, real-time WebSocket communication, and seamless integration with **Slack**, **Discord**, **Email**, **Webhooks**, and custom APIs. Built with FastAPI, LangChain, and Redis for scalable, event-driven agent orchestration.

## Features

### Core Capabilities

- **Unified API Gateway**: Single endpoint for all agent interactions
- **Multi-Channel Integration**: Slack, Discord, Email, SMS, Webhooks
- **Real-Time Communication**: WebSocket support for live updates
- **Event-Driven Architecture**: Webhook handling and event streaming
- **Message Queue**: Redis-based queuing for reliable message delivery
- **Agent Orchestration**: LangChain-based agent integration
- **Rate Limiting & Security**: Production-ready API security
- **Integration Marketplace**: Pre-built connectors and templates

### Supported Integrations

- **Slack**: Bot integration, slash commands, interactive components
- **Discord**: Bot commands, message handling, reactions
- **Email**: SMTP integration, email parsing, automated responses
- **Webhooks**: Incoming/outgoing webhooks, event subscriptions
- **Custom APIs**: REST API integration, custom connectors
- **WebSocket**: Real-time bidirectional communication

## Architecture

```
┌─────────────────┐
│   Frontend UI   │
│   (Streamlit)   │
└────────┬────────┘
         │
┌────────▼─────────────────────────────────────┐
│         API Gateway (FastAPI)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   REST   │  │ WebSocket│  │ Webhooks │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└────────┬─────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────┐
│      Integration Adapters Layer              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│  │Slack │ │Discord│ │Email │ │Custom│       │
│  └──────┘ └──────┘ └──────┘ └──────┘       │
└────────┬─────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────┐
│      Agent Integration Layer                 │
│  ┌──────────────────────────────────────┐   │
│  │     LangChain Agent Orchestrator     │   │
│  └──────────────────────────────────────┘   │
└────────┬─────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────┐
│      Infrastructure Layer                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Redis   │  │PostgreSQL│  │  Queue   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Redis (for message queuing)
- PostgreSQL (optional, SQLite by default)

### Installation

1. **Clone and navigate to the project**:
```bash
cd agent_integration_hub
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

4. **Initialize database**:
```bash
python -m backend.core.database init
```

5. **Start Redis** (if not running):
```bash
# macOS/Linux
redis-server

# Windows (using Docker)
docker run -d -p 6379:6379 redis:alpine
```

6. **Run the API server**:
```bash
uvicorn backend.api.main:app --reload --port 8000
```

7. **Run the frontend** (in another terminal):
```bash
streamlit run frontend/app.py
```

## Usage

### API Gateway

The API gateway provides a unified interface for all agent interactions:

```python
import requests

# Send message to agent via API
response = requests.post(
    "http://localhost:8000/api/v1/agents/chat",
    json={
        "message": "What's the weather today?",
        "channel": "slack",
        "user_id": "user123"
    },
    headers={"Authorization": "Bearer your-api-key"}
)
```

### WebSocket Connection

Connect for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Integration Setup

#### Slack Integration

1. Create a Slack app at https://api.slack.com/apps
2. Add bot token and signing secret to `.env`
3. Configure event subscriptions and slash commands
4. Install app to your workspace

#### Discord Integration

1. Create a Discord application at https://discord.com/developers/applications
2. Add bot token to `.env`
3. Invite bot to your server with appropriate permissions

#### Email Integration

1. Configure SMTP settings in `.env`
2. For Gmail, use an App Password
3. Test connection via the admin dashboard

## Project Structure

```
agent_integration_hub/
├── backend/
│   ├── api/              # FastAPI routes and endpoints
│   ├── core/             # Core functionality (database, config)
│   ├── integrations/     # Integration adapters
│   ├── agents/           # Agent integration layer
│   ├── services/         # Business logic services
│   ├── models/           # Data models
│   └── utils/            # Utility functions
├── frontend/             # Streamlit dashboard
├── tests/                # Test suite
├── data/                 # Database and data files
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Features in Detail

### 1. Unified API Gateway

- Single endpoint for all agent interactions
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and throttling
- Request/response logging

### 2. Multi-Channel Integration

- **Slack**: Full bot integration with events, commands, and interactions
- **Discord**: Bot commands, message handling, and reactions
- **Email**: SMTP integration with parsing and automated responses
- **Webhooks**: Bidirectional webhook support
- **Custom APIs**: Extensible connector framework

### 3. Real-Time Communication

- WebSocket server for live updates
- Event streaming
- Real-time notifications
- Bidirectional communication

### 4. Message Queue

- Redis-based queuing
- Reliable message delivery
- Retry logic
- Dead letter queue

### 5. Agent Orchestration

- LangChain agent integration
- Multi-agent coordination
- Context management
- Tool integration

## Configuration

See `env.example` for all configuration options. Key settings:

- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `API_SECRET_KEY`: Secret key for API authentication
- Integration-specific credentials (Slack, Discord, Email)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black backend/ frontend/
isort backend/ frontend/
```

## 🛠️ Tech Stack

- **Framework**: FastAPI (async Python web framework)
- **Agent Framework**: LangChain (agent orchestration)
- **Message Queue**: Redis (reliable message delivery)
- **Database**: PostgreSQL/SQLite (persistence)
- **Real-time**: WebSockets (bidirectional communication)
- **Integrations**: Slack SDK, Discord.py, SMTP
- **Frontend**: Streamlit (admin dashboard)

## 📈 Use Cases

- **Multi-Channel Customer Support**: Deploy AI agents across Slack, Discord, Email
- **Internal Team Bots**: Productivity bots for Slack/Discord workspaces
- **Email Automation**: Automated email responses and processing
- **Webhook Processing**: Connect AI agents to any webhook-based service
- **Integration Platform**: Build custom connectors for any API
- **Real-Time Chat**: Live chat applications with WebSocket support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [LangChain](https://www.langchain.com/) for agent orchestration
- [Redis](https://redis.io/) for message queuing
- Integration SDKs: Slack, Discord, and the open-source community

