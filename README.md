# Agentic Logger

Logs your clipboard, active window and shell commands to PostgreSQL, adds local LLM
summaries with Ollama, and shows it all in a Flask + React dashboard.

## Services

| Service | Port | Function |
|---------|------|----------|
| UI | 3000 | React dashboard |
| API Backend | 8000 | Flask REST API |
| PostgreSQL | 5432 | Event & session storage |
| Redis | 6379 | Cache & message broker |

All ports are published on 127.0.0.1 only.

## Quick Start

```bash
./setup.sh
```

Capture runs on your machine, not in Docker:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt
python local_agent_runner.py
```

Settings, as environment variables:

- `OLLAMA_MODEL`, default `qwen3.5:4b`
- `OLLAMA_URL`, default `http://localhost:11434`
- `POSTGRES_PASSWORD`, default `postgres`
- `POSTGRES_URL`, used by the runner
- `CORS_ORIGINS`, comma separated
- `IMAGE_DIR`, where copied images are kept

Needed on your machine:

- `xclip` or `wl-clipboard` for the clipboard
- `tesseract-ocr` for text from copied images
- `xdotool` for window tracking on X11
- The Window Calls GNOME extension for window tracking on GNOME Wayland

Text that looks like a credential is replaced with a placeholder before saving.
The API has no login, so keep it on localhost.

## API Endpoints

### Events
- `POST /api/events` - Create event
- `GET /api/events` - List events
- `GET /api/events/<id>` - Get event

### Sessions
- `POST /api/sessions` - Start session
- `GET /api/sessions/<agent_id>` - Get session
- `PUT /api/sessions/<agent_id>` - Update session

### Stats
- `GET /api/stats/summary` - Get statistics

### Activity
- `GET /api/clipboard`, `/api/activity`, `/api/commands` - List captured events
- `GET /api/stats` - Capture statistics
- `POST /api/search` - Search all captured events
- `POST /api/search/semantic`, `/api/search/keywords` - Search clipboard events

### Health
- `GET /health` - Health check

## Next Steps

1. `./setup.sh` - Initialize infrastructure
2. `docker compose logs -f` - Monitor startup
3. `curl http://localhost:8000/health` - Verify API
4. Visit `http://localhost:3000` - Frontend UI
