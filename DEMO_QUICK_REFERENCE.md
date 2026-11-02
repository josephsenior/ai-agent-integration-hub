# 🚀 Demo Quick Reference Card

## ⚡ Quick Start
```powershell
# Backend
cd agent_integration_hub
.\.venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend-nextjs
npm run dev
```

## 🔗 URLs
- Frontend: **http://localhost:3000**
- Backend: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**
- Health: **http://localhost:8000/health**

---

## 🎯 Key Talking Points

### Opening (30 seconds)
> "AI Agent Integration Hub - unified platform connecting AI agents to Slack, Discord, Email, and Webhooks through a single API gateway."

### Problem Statement
> "Companies need AI agents across multiple channels, but each requires separate setup. This platform provides one unified solution."

### Solution
> "Write your agent once, deploy it everywhere. Same logic works across all channels."

### Tech Stack
> "FastAPI backend, Next.js frontend, LangChain agents, Redis queuing - all production-ready."

---

## 📋 Demo Flow (15 min)

1. **Intro** (2 min) - Problem, solution, architecture
2. **Frontend Tour** (3 min) - Chat, Messages, Integrations, Analytics
3. **API Demo** (3 min) - Swagger UI, health check, chat endpoint
4. **Integrations** (4 min) - Slack, Discord, Email, Webhooks
5. **Technical** (3 min) - Architecture, scalability, security

---

## 💬 Sample Messages to Send

### Test Message 1
```
"Hello, can you explain how this integration platform works?"
```

### Test Message 2
```
"What channels can I integrate with?"
```

### Test Message 3
```
"Show me the available integrations"
```

---

## 🔑 Key Features to Highlight

✅ **Unified API Gateway** - Single endpoint for all channels  
✅ **Multi-Channel** - Slack, Discord, Email, Webhooks  
✅ **Real-Time** - WebSocket support  
✅ **Event-Driven** - Redis pub/sub  
✅ **Production-Ready** - Security, logging, error handling  
✅ **Extensible** - Easy to add new integrations  

---

## 🎤 Common Questions & Answers

**Q: How does it scale?**  
A: "Horizontal scaling with Redis queuing and stateless API. Can handle thousands of concurrent connections."

**Q: Is it secure?**  
A: "Operator login uses a signed, short-lived HttpOnly cookie with CSRF checks. Login throttling and multi-operator support remain future work."

**Q: Can I add custom integrations?**  
A: "Yes! Adapter pattern makes it easy. Each integration is a module implementing a common interface."

**Q: What agent frameworks work?**  
A: "Agent-agnostic. Works with LangChain, but you can plug in any framework or model."

**Q: How do you deploy it?**  
A: "Dockerized. Can deploy with Docker Compose or Kubernetes for production."

---

## 🐛 Quick Fixes

**Backend won't start?**
- Check port 8000: `netstat -ano | findstr :8000`
- Check Redis: `redis-cli ping`

**Frontend won't start?**
- Clear cache: `Remove-Item -Recurse -Force .next`
- Reinstall: `npm install`

**WebSocket fails?**
- Check operator credentials and session signing key in backend `.env`
- Verify backend on port 8000

**Agent not responding?**
- Check GEMINI_API_KEY in `.env`
- Check backend logs

---

## 📊 Architecture (One-Liner)

```
Frontend → API Gateway → Integrations → Agents → Redis/DB
```

**Explain**: "Layered architecture with clear separation of concerns. Each layer is independently scalable."

---

## 🎯 Use Cases (Quick List)

1. **Multi-Channel Support** - Same agent, all channels
2. **Team Bots** - Slack/Discord productivity bots
3. **Email Automation** - 24/7 email responses
4. **Webhook Processing** - Connect to any service
5. **Integration Platform** - Build custom connectors

---

## ⚠️ Things to Avoid

❌ Don't go too deep into code during demo  
❌ Don't show errors (have backup plan)  
❌ Don't rush - pause between sections  
❌ Don't forget to show the UI (it's beautiful!)  

---

## ✅ Demo Checklist

- [ ] Backend running (port 8000)
- [ ] Frontend running (port 3000)
- [ ] Redis running
- [ ] Operator login configured
- [ ] Browser ready
- [ ] API docs tab open
- [ ] Terminal logs visible

---

**Keep this open during your demo! 📌**
