# Testing Guide - Next.js Frontend

## Pre-Testing Checklist

### 1. Verify Backend is Running

```bash
# In agent_integration_hub directory
# Make sure backend is running on port 8000
uvicorn backend.api.main:app --reload --port 8000
```

Test backend health:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "timestamp": "..."
}
```

### 2. Check Environment Variables

Create `.env.local` in `frontend-nextjs/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. Install Dependencies

```bash
cd frontend-nextjs
npm install
```

## Testing Steps

### Step 1: Start Development Server

```bash
npm run dev
```

Expected output:
```
▲ Next.js 14.0.4
- Local:        http://localhost:3000
```

### Step 2: Open Browser

Navigate to: http://localhost:3000

### Step 3: Test Settings Configuration

1. Click "Settings" button in header
2. Verify API URL is `http://localhost:8000`
3. Sign in with `OPERATOR_USERNAME` and the original password used to generate `OPERATOR_PASSWORD_HASH`
4. Click "Test Connection"
5. Should see: `✅ Connected - Redis: connected`
6. Click "Save"

### Step 4: Test WebSocket Connection

1. Check header for connection status indicator
2. Should show green dot with "Connected"
3. Open browser console (F12)
4. Should see: `WebSocket connected`

### Step 5: Test Chat Functionality

1. Go to "💬 Chat" tab
2. Select channel (default: "api")
3. Type a message: "Hello, test message"
4. Click Send or press Enter
5. Should see:
   - Your message appears on right side
   - Loading indicator
   - Agent response appears on left side

### Step 6: Test Message History

1. Go to "📨 Messages" tab
2. Click "Refresh" button
3. Should see list of messages
4. Test filters:
   - Change channel filter
   - Change status filter
   - Change limit

### Step 7: Test Integrations Tab

1. Go to "🔌 Integrations" tab
2. Should see 5 integration cards:
   - Slack, Discord, Email, Webhook, WebSocket
3. WebSocket should show "Connected" status

### Step 8: Test Analytics Tab

1. Go to "📊 Analytics" tab
2. Should see metrics:
   - Total Messages
   - Completed
   - Failed
   - Pending
3. Should see "Messages by Channel" chart

## Common Issues & Solutions

### Issue: WebSocket not connecting

**Symptoms:**
- Red dot in header
- Console shows connection errors

**Solutions:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify WebSocket URL in `.env.local`: `ws://localhost:8000`
3. Check browser console for specific error
4. Verify backend WebSocket endpoint is `/ws` (not `/ws/`)

### Issue: API requests failing

**Symptoms:**
- "Error: HTTP error! status: 401"
- Messages not loading

**Solutions:**
1. Verify the operator credentials and session signing key are configured on the backend
2. Check operator credentials and `SESSION_SECRET_KEY` in backend `.env`
3. Test connection in Settings modal
4. Check browser Network tab for request details

### Issue: Build errors

**Symptoms:**
- `npm run dev` fails
- TypeScript errors

**Solutions:**
1. Clear `.next` folder: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check Node.js version: `node --version` (should be 18+)

### Issue: Styles not loading

**Symptoms:**
- Page looks unstyled
- Tailwind classes not working

**Solutions:**
1. Verify `tailwind.config.ts` exists
2. Check `postcss.config.js` exists
3. Restart dev server
4. Clear browser cache

## Browser Console Checks

Open browser console (F12) and verify:

✅ No red errors
✅ WebSocket connection message
✅ API requests returning 200 status
✅ No CORS errors

## Network Tab Checks

Open Network tab (F12) and verify:

✅ Health check request succeeds
✅ Chat API requests succeed (200 status)
✅ WebSocket connection established (101 status)
✅ No failed requests

## Expected Behavior

### Chat Tab
- ✅ Messages appear instantly
- ✅ Loading state shows while processing
- ✅ Error messages display if API fails
- ✅ Channel selection works
- ✅ User ID and Channel ID inputs work

### Messages Tab
- ✅ Messages load on page open
- ✅ Filters work correctly
- ✅ Refresh button updates list
- ✅ Message details expand correctly

### Integrations Tab
- ✅ All integrations display
- ✅ Status indicators show correctly
- ✅ WebSocket shows connected

### Analytics Tab
- ✅ Metrics calculate correctly
- ✅ Charts display properly
- ✅ Data updates when messages change

## Performance Checks

1. **Page Load**: Should be < 2 seconds
2. **Chat Response**: Should be < 3 seconds (depends on backend)
3. **Message History**: Should load < 1 second
4. **WebSocket Reconnect**: Should reconnect automatically if connection drops

## Next Steps After Testing

If all tests pass:
1. ✅ Frontend is ready for demo
2. ✅ Can proceed with recording
3. ✅ Consider adding more features

If issues found:
1. Check error messages in console
2. Verify backend configuration
3. Review this guide for solutions
4. Check backend logs for errors
