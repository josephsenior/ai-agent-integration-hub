# Agent Integration Hub - Next.js Frontend

Modern React/Next.js frontend for the AI Agent Integration Hub, featuring real-time WebSocket communication, modern UI components, and comprehensive integration management.

## Features

- 🚀 **Next.js 14** with App Router
- ⚡ **Real-time WebSocket** communication
- 🎨 **Modern UI** with Tailwind CSS
- 📊 **Analytics Dashboard** with live metrics
- 💬 **Chat Interface** with multi-channel support
- 📨 **Message History** with filtering
- 🔌 **Integration Management** dashboard
- ⚙️ **Settings** for API configuration

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000` (or configure via environment variables)

### Installation

```bash
cd frontend-nextjs
npm install
```

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend-nextjs/
├── app/                 # Next.js app directory
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Main page with tabs
│   └── globals.css     # Global styles
├── components/          # React components
│   ├── layout.tsx      # Main layout with header
│   ├── chat-tab.tsx    # Chat interface
│   ├── messages-tab.tsx # Message history
│   ├── integrations-tab.tsx # Integration management
│   ├── analytics-tab.tsx   # Analytics dashboard
│   └── settings-modal.tsx   # Settings modal
├── lib/                # Utilities
│   ├── api.ts          # API client
│   ├── websocket.ts    # WebSocket client
│   └── utils.ts        # Helper functions
├── store/              # State management
│   └── config-store.ts # Configuration store
└── types/              # TypeScript types
    └── index.ts        # Type definitions
```

## Usage

1. **Configure API**: Set the backend URL in Settings and sign in with the configured operator account
2. **Chat**: Use the Chat tab to send messages to agents via different channels
3. **Messages**: View message history with filtering options
4. **Integrations**: Monitor integration status and configuration
5. **Analytics**: View metrics and statistics

## WebSocket Features

The frontend automatically connects to the WebSocket endpoint for real-time updates:

- Real-time message responses
- Connection status indicator
- Event broadcasting
- Automatic reconnection

## API Integration

The frontend uses the following API endpoints:

- `GET /health` - Health check
- `POST /api/v1/agents/chat` - Send message to agent
- `GET /api/v1/messages` - List messages
- `GET /api/v1/messages/{id}` - Get message by ID
- `WS /ws` - WebSocket connection

## Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Query** - Data fetching
- **Zustand** - State management
- **Reconnecting WebSocket** - WebSocket client

## License

MIT
