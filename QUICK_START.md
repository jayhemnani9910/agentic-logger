# Quick Start - Agentic Logger

## Run Everything
```bash
cd /home/jey/jh-core/agentic_logger
docker compose up -d
```

## Check Status
```bash
docker compose ps
```

## Access Services
- **Backend API**: http://localhost:8000
- **Frontend Dashboard**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Test API
```bash
# Health
curl http://localhost:8000/health

# Create event
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test",
    "agent_id": "agent_001",
    "message": "Test event",
    "data": {},
    "status": "completed"
  }'

# Get events
curl http://localhost:8000/api/events
```

## Stop Everything
```bash
docker compose down
```

## View Logs
```bash
docker compose logs -f backend    # Backend
docker compose logs -f ui         # Frontend
docker compose logs -f postgres   # Database
docker compose logs -f redis      # Cache
```

## Troubleshoot
```bash
# Reset everything
docker compose down -v
docker compose build
docker compose up -d

# Check specific service
docker compose logs <service_name>

# Rebuild backend
docker compose build backend
docker compose restart backend
```

## Core Services
- ✅ Backend (Flask Python)
- ✅ Frontend (React Node.js)
- ✅ PostgreSQL Database
- ✅ Redis Cache

All tested and working!
