#!/bin/bash
# reset_test_env.sh - Reset Docker environment to clear rate limiting

echo "🔄 Resetting DataPulse test environment..."

# Stop containers
echo "⏹️ Stopping containers..."
docker-compose down

# Remove volumes (clears rate limiting data)
echo "🗑️ Removing volumes..."
docker-compose down -v

# Remove images to force rebuild
echo "🔨 Rebuilding images..."
docker-compose build --no-cache

# Start fresh
echo "🚀 Starting fresh environment..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Check if API is ready
echo "🔍 Checking API status..."
curl -f http://localhost:8000/ || echo "API not ready yet"

echo "✅ Environment reset complete!"
echo "💡 Rate limiting should be cleared now"
