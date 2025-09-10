#!/bin/bash

# Smart deployment script - only rebuilds what changed

echo "🚀 Deploying Zero-Downtime Pipeline..."

# Pull latest changes
echo "📥 Pulling latest code..."
git pull

# Check what changed
CHANGED_FILES=$(git diff HEAD~1 --name-only)

# Check if backend code changed
if echo "$CHANGED_FILES" | grep -q "apps/"; then
    echo "🔨 Backend changes detected - rebuilding images..."
    docker-compose up -d --build
elif echo "$CHANGED_FILES" | grep -q "frontend/"; then
    echo "🎨 Frontend changes only - restarting nginx..."
    docker-compose restart frontend
else
    echo "📦 Config changes - restarting all services..."
    docker-compose up -d
fi

echo "✅ Deployment complete!"
echo "🌐 Access at: http://localhost"

# Optional: Show running containers
docker ps