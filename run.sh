#!/bin/bash
set -e

# Start services
echo "Starting services..."
cd /home/jey/jh-core/agentic_logger

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Verify setup
echo "Verifying setup..."
sleep 15

# Check endpoints
echo "Testing API endpoint..."
curl -s http://localhost:8000/health | python -m json.tool || echo "API not ready yet"

echo ""
echo "Setup complete! Use these commands:"
echo ""
echo "View logs:           docker-compose logs -f"
echo "Stop services:       docker-compose down"
echo "Restart services:    docker-compose restart"
echo "Remove volumes:      docker-compose down -v"
echo ""
