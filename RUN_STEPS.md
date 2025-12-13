# Agentic Logger - RUN STEPS

## Prerequisites
- Docker & Docker Compose installed
- Ports available: 3000, 8000, 5432, 6379, 9200, 19530

## Quick Start (1 Command)

```bash
cd /home/jey/jh-core/agentic_logger
chmod +x setup.sh
./setup.sh
```

## Services Overview

| Service | URL | Purpose |
|---------|-----|---------|
| API Backend | http://localhost:8000 | Flask REST API |
| Frontend UI | http://localhost:3000 | React Dashboard |
| PostgreSQL | localhost:5432 | Event Database |
| Redis | localhost:6379 | Cache & Message Queue |
| Elasticsearch | http://localhost:9200 | Logging & Search |
| Milvus | localhost:19530 | Vector Database |
| Temporal | localhost:7233 | Workflow Engine |

## Run Commands

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
docker-compose logs -f backend
```

**Stop services:**
```bash
docker-compose down
```

**Remove everything (volumes too):**
```bash
docker-compose down -v
```

**Restart specific service:**
```bash
docker-compose restart backend
```

## Health Checks

**API Health:**
```bash
curl http://localhost:8000/health
```

**Database:**
```bash
docker-compose exec postgres psql -U postgres -d agentic_logger -c "SELECT COUNT(*) FROM events;"
```

**Redis:**
```bash
docker-compose exec redis redis-cli ping
```

## API Usage

**Create event:**
```bash
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "task_start",
    "agent_id": "agent_001",
    "task_id": "task_001",
    "message": "Task started",
    "metadata": {"key": "value"}
  }'
```

**List events:**
```bash
curl "http://localhost:8000/api/events?agent_id=agent_001&limit=10"
```

**Get stats:**
```bash
curl "http://localhost:8000/api/stats/summary?hours=24"
```

**Start session:**
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_001", "metadata": {}}'
```

## Development

**Access logs:**
```bash
docker-compose exec backend tail -f logs/agentic_logger.log
```

**Database shell:**
```bash
docker-compose exec postgres psql -U postgres -d agentic_logger
```

**Redis CLI:**
```bash
docker-compose exec redis redis-cli
```

**Elasticsearch:**
```bash
curl http://localhost:9200/_cat/indices
```

## Troubleshooting

**Port already in use:**
```bash
lsof -i :8000  # Find process
kill -9 <PID>   # Kill it
```

**Services not healthy:**
```bash
docker-compose ps            # Check status
docker-compose logs backend  # Check logs
```

**Database connection failed:**
```bash
docker-compose exec postgres psql -U postgres -c "\l"
```

**Clear data:**
```bash
docker-compose down -v
docker volume prune
```
