# Quick Start Guide - Next.js Frontend

Get the Next.js frontend up and running in 5 minutes!

## Prerequisites

- Node.js 18+ installed
- Backend API running (see main README)

## Steps

### 1. Install Dependencies

```bash
cd frontend-nextjs
npm install
```

### 2. Configure Environment

Create `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

### 4. Sign in

1. Open http://localhost:3000
2. Sign in with `OPERATOR_USERNAME` and the original password used to create the PBKDF2 hash
3. Keep `SESSION_SECRET_KEY` set in the backend environment

### 5. Start Using!

- **Chat Tab**: Send messages to agents
- **Messages Tab**: View message history
- **Integrations Tab**: Monitor integration status
- **Analytics Tab**: View metrics and statistics

## Features

✅ Real-time WebSocket communication  
✅ Modern, responsive UI  
✅ Connection status indicator  
✅ Multi-channel support  
✅ Message filtering and search  
✅ Analytics dashboard  

## Troubleshooting

**WebSocket not connecting?**
- Check backend is running on port 8000
- Verify `NEXT_PUBLIC_WS_URL` in `.env.local`
- Check browser console for errors

**API requests failing?**
- Verify the operator credentials and session signing key are configured on the backend
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Test connection using Settings modal

**Build errors?**
- Clear `.next` folder: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`

## Next Steps

- Read the [Migration Guide](./MIGRATION_GUIDE.md) for details
- Check the [README](./README.md) for full documentation
- Explore the components in `/components` directory
