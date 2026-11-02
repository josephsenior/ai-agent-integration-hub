# Migration Guide: Streamlit to Next.js

This guide explains how to migrate from the Streamlit frontend to the new Next.js frontend.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd frontend-nextjs
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API URL
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Configure API:**
   - Open the app at http://localhost:3000
   - Click "Settings" in the header
   - Sign in using the operator username and password from backend `.env`

## Key Differences

### Architecture
- **Streamlit**: Python-based, server-side rendering
- **Next.js**: React-based, client-side rendering with SSR

### Real-time Features
- **Streamlit**: Limited WebSocket support
- **Next.js**: Full WebSocket integration with automatic reconnection

### State Management
- **Streamlit**: Session state (server-side)
- **Next.js**: React Query + Zustand (client-side)

### API Integration
- **Streamlit**: Direct Python API calls
- **Next.js**: REST API client with React Query caching

## Features Comparison

| Feature | Streamlit | Next.js |
|---------|-----------|---------|
| Chat Interface | ✅ | ✅ |
| Message History | ✅ | ✅ |
| Integration Management | ✅ | ✅ |
| Analytics | Basic | Enhanced |
| WebSocket Real-time | ❌ | ✅ |
| Settings UI | Basic | Enhanced |
| Connection Status | ❌ | ✅ |

## Migration Steps

### 1. Keep Backend Running
The backend API remains unchanged. Both frontends can work with the same backend.

### 2. Update Environment Variables
The Next.js frontend uses different environment variable names:
- `NEXT_PUBLIC_API_URL` instead of hardcoded URL
- `NEXT_PUBLIC_WS_URL` for WebSocket URL

### 3. Operator Session
- Set `OPERATOR_USERNAME`, `OPERATOR_PASSWORD_HASH`, and `SESSION_SECRET_KEY` on the backend.
- The Next.js dashboard receives an HttpOnly session cookie; it does not store a shared API key.

### 4. WebSocket Usage
The dashboard WebSocket uses the operator session cookie and checks the configured origin.

## Running Both Frontends

You can run both frontends simultaneously for comparison:

```bash
# Terminal 1: Streamlit
cd frontend
streamlit run app.py

# Terminal 2: Next.js
cd frontend-nextjs
npm run dev
```

- Streamlit: http://localhost:8501
- Next.js: http://localhost:3000

## Benefits of Next.js Frontend

1. **Better Performance**: Client-side rendering, faster interactions
2. **Real-time Updates**: Full WebSocket support with live status
3. **Modern UI**: Better UX with Tailwind CSS
4. **Type Safety**: Full TypeScript support
5. **Production Ready**: Better suited for production deployment
6. **Extensibility**: Easier to add new features and components

## Troubleshooting

### WebSocket Connection Issues
- Check that backend is running on correct port
- Verify `NEXT_PUBLIC_WS_URL` in `.env.local`
- Check browser console for WebSocket errors

### API Connection Issues
- Verify the operator credentials and session signing key are configured on the backend
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Test connection using "Test Connection" button in Settings

### Build Issues
- Ensure Node.js 18+ is installed
- Clear `.next` folder and rebuild: `rm -rf .next && npm run build`

## Next Steps

1. Test all features in the new frontend
2. Compare with Streamlit version
3. Deploy Next.js frontend to production
4. Consider deprecating Streamlit frontend (optional)
