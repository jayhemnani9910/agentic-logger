# Contributing

Thanks for helping. I reply to issues within 24 hours.

## Set up

```bash
git clone https://github.com/jayhemnani9910/agentic-logger
cd agentic-logger
./setup.sh      # dashboard, API and database in Docker
./capture.sh    # capture on your machine, needs Python 3.11 or uv
```

## Run the checks

These are the same checks CI runs, from the repo root after `./capture.sh` has made `.venv`:

```bash
.venv/bin/python -m pytest tests
ruff check --isolated --select F,E9 backend local_agent_runner.py tests
npx pyright --pythonpath .venv/bin/python
cd frontend && npm ci && CI=true npm run build
```

Please use made-up data in tests and screenshots, never your real clipboard or shell history.

## Code style

Match the code around your change, and keep it simple.

## Pull requests

- Branch from `master`, with one change per pull request.
- Add a test when you fix a bug.
- Do not skip or loosen a test to make it pass.

## Reporting bugs

Open an [issue](https://github.com/jayhemnani9910/agentic-logger/issues/new/choose) with the steps to reproduce it, what you expected, your OS and your desktop session (X11 or Wayland).
Report security problems privately through GitHub's "Report a vulnerability" button, not in a public issue.
