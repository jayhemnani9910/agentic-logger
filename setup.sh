#!/bin/bash
set -e

# Setup script for agentic logger

echo "🚀 Starting Agentic Logger Setup..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker found"

# Create necessary directories
mkdir -p backend/logs
mkdir -p frontend
mkdir -p data/{redis,elasticsearch,postgres,milvus}

echo "✅ Directories created"

# Copy env file if not exists
if [ ! -f .env ]; then
    echo "⚠️  .env not found, creating from template..."
    cat > .env << 'EOF'
FLASK_ENV=production
POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/agentic_logger
REDIS_URL=redis://redis:6379
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
WORKERS=4
TIMEOUT=120
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-change-in-production
EOF
fi

echo "✅ Environment configured"

# Build images
echo "🔨 Building Docker images..."
docker-compose build

echo "✅ Images built successfully"

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Services started"

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Checking health..."
docker-compose ps

echo ""
echo "════════════════════════════════════════"
echo "✅ Setup Complete!"
echo "════════════════════════════════════════"
echo ""
echo "Services running:"
echo "  API:           http://localhost:8000"
echo "  UI:            http://localhost:3000"
echo "  Elasticsearch: http://localhost:9200"
echo "  Redis:         localhost:6379"
echo "  PostgreSQL:    localhost:5432"
echo "  Milvus:        localhost:19530"
echo ""
echo "Next steps:"
echo "  1. Run: docker-compose logs -f"
echo "  2. Visit: http://localhost:3000"
echo ""
