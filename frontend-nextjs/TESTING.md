# Testing Guide - Next.js Frontend

## Quick Test Checklist

### ✅ Pre-Testing Setup

1. **Backend Running?**
   ```bash
   # In agent_integration_hub directory
   uvicorn backend.api.main:app --reload --port 8000
   ```
   Test: `curl http://localhost:8000/health`

2. **Dependencies Installed?**
   ```bash
   cd frontend-nextjs
   npm install
   ```

3. **Environment Configured?**
   ```bash
   # Create .env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

### 🚀 Start Testing

```bash
npm run dev
```

Open: http://localhost:3000

## Test Scenarios

### 1. Settings & Configuration ✅

**Steps:**
1. Click "Settings" in header
2. Verify API URL: `http://localhost:8000`
3. Sign in with `OPERATOR_USERNAME` and the original password used to generate `OPERATOR_PASSWORD_HASH`
4. Click "Test Connection"
5. Should see: `✅ Connected - Redis: connected`
6. Click "Save"

**Expected:** API URL saved; session cookie is issued after sign-in

---

### 2. WebSocket Connection ✅

**Steps:**
1. Check header for connection indicator
2. Should show green dot + "Connected"
3. Open browser console (F12)
4. Should see: `WebSocket connected`

**Expected:** WebSocket status shows connected

**If disconnected:**
- Check backend is running
- Verify WebSocket URL in `.env.local`
- Check browser console for errors

---

### 3. Chat Functionality ✅

**Steps:**
1. Go to "💬 Chat" tab
2. Select channel: "api" (default)
3. Type: "Hello, this is a test"
4. Click Send or press Enter
5. Wait for response

**Expected:**
- Your message appears on right (blue)
- Loading indicator shows
- Agent response appears on left (gray)
- Response contains text

**If fails:**
- Check operator credentials and session secret are configured
- Check browser console for errors
- Verify backend is processing requests

---

### 4. Message History ✅

**Steps:**
1. Go to "📨 Messages" tab
2. Click "Refresh" button
3. Should see list of messages
4. Test filters:
   - Change "Channel" filter
   - Change "Status" filter
   - Change "Limit" number

**Expected:**
- Messages load successfully
- Filters work correctly
- Message details show correctly

---

### 5. Integrations Tab ✅

**Steps:**
1. Go to "🔌 Integrations" tab
2. Check all 5 integrations display:
   - Slack
   - Discord
   - Email
   - Webhook
   - WebSocket

**Expected:**
- All integrations show
- WebSocket shows "Connected" status
- Status indicators are correct

---

### 6. Analytics Tab ✅

**Steps:**
1. Go to "📊 Analytics" tab
2. Check metrics display:
   - Total Messages
   - Completed
   - Failed
   - Pending
3. Check "Messages by Channel" chart

**Expected:**
- Metrics calculate correctly
- Chart displays properly
- Data updates when messages change

---

## Browser Console Checks

Open DevTools (F12) → Console tab:

✅ **Should see:**
- `WebSocket connected`
- No red errors
- API requests returning 200

❌ **Should NOT see:**
- CORS errors
- WebSocket connection errors
- 401 Unauthorized errors
- 404 Not Found errors

---

## Network Tab Checks

Open DevTools (F12) → Network tab:

✅ **Check these requests:**
1. `/health` → Status 200
2. `/api/v1/agents/chat` → Status 200 (when sending message)
3. `/api/v1/messages` → Status 200 (when loading messages)
4. WebSocket → Status 101 (Switching Protocols)

---

## Common Issues & Fixes

### ❌ WebSocket Not Connecting

**Symptoms:** Red dot, "Disconnected" status

**Fixes:**
1. Backend running? `curl http://localhost:8000/health`
2. Check `.env.local`: `NEXT_PUBLIC_WS_URL=ws://localhost:8000`
3. Backend WebSocket is on same port as API (8000), not 8001
4. Check browser console for specific error

---

### ❌ API Requests Failing (401)

**Symptoms:** "Error: HTTP error! status: 401"

**Fixes:**
1. Operator credentials configured in backend `.env`?
2. Operator credentials and `SESSION_SECRET_KEY` match backend `.env`?
3. Test connection in Settings modal
4. Check Network tab → Request Headers → Authorization

---

### ❌ Messages Not Loading

**Symptoms:** Empty message list, loading forever

**Fixes:**
1. Operator session active?
2. Backend database initialized?
3. Check Network tab for failed requests
4. Try refreshing page

---

### ❌ Build/Compile Errors

**Symptoms:** `npm run dev` fails, TypeScript errors

**Fixes:**
1. Clear cache: `rm -rf .next`
2. Reinstall: `rm -rf node_modules && npm install`
3. Check Node version: `node --version` (need 18+)
4. Check TypeScript errors in terminal

---

### ❌ Styles Not Loading

**Symptoms:** Unstyled page, Tailwind not working

**Fixes:**
1. Verify `tailwind.config.ts` exists
2. Verify `postcss.config.js` exists
3. Restart dev server
4. Hard refresh browser (Ctrl+Shift+R)

---

## Performance Checks

✅ **Page Load:** < 2 seconds
✅ **Chat Response:** < 3 seconds (depends on backend/LLM)
✅ **Message History:** < 1 second
✅ **WebSocket Reconnect:** Automatic if connection drops

---

## Success Criteria

✅ All tabs load without errors
✅ WebSocket connects and shows green status
✅ Chat sends and receives messages
✅ Message history loads and filters work
✅ Integrations tab shows all integrations
✅ Analytics tab shows metrics
✅ Settings save and test connection works
✅ No console errors
✅ No network errors

---

## Next Steps After Testing

If all tests pass:
1. ✅ Ready for demo recording!
2. ✅ Can proceed with production build
3. ✅ Consider adding more features

If issues found:
1. Check error messages in console
2. Review this guide for solutions
3. Check backend logs
4. Verify environment configuration

---

## Manual Test Script

Run this in browser console to test API:

```javascript
// Test API connection
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);

// Test WebSocket (if connected)
// Check Network tab for WebSocket connection
```

---

## Automated Test (Optional)

```bash
# Test backend connection
npm run test:connection
```

This will verify:
- ✅ Health endpoint works
- ✅ WebSocket connects
- ✅ Backend is ready
