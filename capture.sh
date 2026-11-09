#!/bin/bash
# Start capturing on this machine. Installs what it needs on first run.
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo "First run: installing capture dependencies (a few minutes)..."
    if command -v uv &> /dev/null; then
        uv venv --python 3.11 .venv
        PIP=(uv pip install --python .venv/bin/python)
    else
        python3.11 -m venv .venv
        PIP=(.venv/bin/pip install)
    fi
    "${PIP[@]}" torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
    "${PIP[@]}" -r backend/requirements.txt
fi

exec .venv/bin/python local_agent_runner.py
