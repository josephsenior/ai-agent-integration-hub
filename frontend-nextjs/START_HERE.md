# 🚀 Start Here - Testing the Next.js Frontend

## Quick Start (3 Steps)

### 1️⃣ Install Dependencies
```bash
cd agent_integration_hub/frontend-nextjs
npm install
```

### 2️⃣ Start Backend (Terminal 1)
```bash
cd agent_integration_hub
uvicorn backend.api.main:app --reload --port 8000
```

### 3️⃣ Start Frontend (Terminal 2)
```bash
cd agent_integration_hub/frontend-nextjs
npm run dev
```

Then open: **http://localhost:3000**

---

## First Time Setup

### Sign in

1. Open http://localhost:3000
2. Sign in using `OPERATOR_USERNAME` and the password used to generate `OPERATOR_PASSWORD_HASH`
3. The backend must also have `SESSION_SECRET_KEY` configured

---

## Quick Test

### Test Chat
1. Go to **"💬 Chat"** tab
2. Type: `Hello, this is a test`
3. Press **Enter**
4. Wait for agent response

### Verify WebSocket
- Check header: Should show **🟢 green dot** + "Connected"
- If red dot: Check backend is running

---

## What to Test

✅ **Operator sign-in** - Authenticate using the backend session  
✅ **Chat** - Send messages, get responses  
✅ **Messages** - View history, test filters  
✅ **Integrations** - See integration status  
✅ **Analytics** - View metrics  

---

## Troubleshooting

**WebSocket not connecting?**
- Backend running? Check: `curl http://localhost:8000/health`
- Check `.env.local` exists with correct URLs

**API errors?**
- `OPERATOR_USERNAME`, `OPERATOR_PASSWORD_HASH`, and `SESSION_SECRET_KEY` configured?
- Test connection in Settings modal

**Build errors?**
```bash
rm -rf .next node_modules
npm install
npm run dev
```

---

## Full Testing Guide

See [TESTING.md](./TESTING.md) for comprehensive testing steps.

See [QUICK_TEST.md](./QUICK_TEST.md) for 5-minute quick test.

---

## Success! 🎉

If everything works:
- ✅ WebSocket shows green "Connected"
- ✅ Chat sends and receives messages
- ✅ No errors in browser console
- ✅ All tabs load correctly

**You're ready to demo!** 🚀
