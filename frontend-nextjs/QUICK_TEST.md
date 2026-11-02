# Quick Test Guide

## 🚀 5-Minute Test

### Step 1: Start Backend (Terminal 1)
```bash
cd agent_integration_hub
uvicorn backend.api.main:app --reload --port 8000
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### Step 2: Start Frontend (Terminal 2)
```bash
cd agent_integration_hub/frontend-nextjs
npm install  # First time only
npm run dev
```

Wait for: `Local: http://localhost:3000`

### Step 3: Open Browser
Go to: **http://localhost:3000**

### Step 4: Sign in
1. Set `OPERATOR_USERNAME`, `OPERATOR_PASSWORD_HASH`, and `SESSION_SECRET_KEY` in backend `.env`
2. Sign in on the dashboard with the configured username and password

### Step 5: Test Chat
1. Go to **"💬 Chat"** tab
2. Type: `Hello, test message`
3. Press **Enter** or click **Send**
4. Wait for response (may take a few seconds)

### Step 6: Live updates
- The dashboard WebSocket uses the operator session cookie and checks the configured origin.

## ✅ Success Indicators

- ✅ Operator sign-in succeeds
- ✅ Chat messages send and receive
- ✅ No red errors in browser console
- ✅ Settings save successfully

## ❌ If Something Fails

**API errors?**
- Check the operator credentials and session secret in backend `.env`
- Test connection in Settings modal

**Build errors?**
```bash
rm -rf .next node_modules
npm install
npm run dev
```

## 📋 Full Test Checklist

See [TESTING.md](./TESTING.md) for comprehensive testing guide.
