# Agentic Logger Workflow

```
USER ACTION → CLIPBOARD → AGENT ORCHESTRATOR → LLM PROCESSOR → DATABASE → FRONTEND

📋 Copy Text
     ↓
🖥️  Clipboard Watcher detects change
     ↓
🚀 Event Orchestrator receives event
     ↓
🤖 LLM Processor analyzes content
     ↓
💾 Save to PostgreSQL
     ↓
🌐 Frontend displays via API
```

## Current State

```
❌ Docker Backend: xclip not available → agents stop → no data saved
✅ Docker Database: Working
✅ Docker Frontend: Working

✅ Local Backend: xclip available → agents work → data saved
```

## Solution

```
Stop: docker compose stop backend
Run:  Local backend + Docker database/redis
Result: Agents work → data saved → frontend shows data
```