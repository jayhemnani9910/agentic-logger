#!/bin/bash
# Run backend locally while keeping database in Docker

echo "🚀 Starting Agentic Logger Backend (Local Mode)"
echo "Database and Redis will remain in Docker containers"

# Check if Docker containers are running
if ! docker compose ps | grep -q "Up"; then
    echo "❌ Docker containers are not running. Please run: docker compose up -d"
    exit 1
fi

# Set environment variables
export FLASK_ENV=development
export POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/agentic_logger
export REDIS_URL=redis://localhost:6379
export LOG_LEVEL=INFO

# Create logs directory
mkdir -p logs

echo "📋 Starting Flask development server..."
echo "🌐 API will be available at: http://localhost:5000"
echo "🖥️  Frontend should connect to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"

# Run Flask development server
python app.py