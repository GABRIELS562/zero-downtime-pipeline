#!/bin/bash

# Build and push Finance Trading app to local registry
# This script builds the Docker image and pushes it to localhost:5000 for Kubernetes

set -e

# Configuration
REGISTRY="localhost:5000"
APP_NAME="finance-app"
TAG="${1:-production}"
BUILD_ID=$(date +%Y%m%d-%H%M%S)
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "💹 Building Finance Trading Application"
echo "Registry: $REGISTRY"
echo "Tag: $TAG"
echo "Build ID: $BUILD_ID"
echo "Git Commit: $GIT_COMMIT"

# Build the Docker image with production target
echo "📦 Building Docker image..."
docker build \
    --target production \
    --build-arg BUILD_ID="$BUILD_ID" \
    --build-arg GIT_COMMIT="$GIT_COMMIT" \
    --build-arg BUILD_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    -t "$REGISTRY/$APP_NAME:$TAG" \
    -t "$REGISTRY/$APP_NAME:$BUILD_ID" \
    -t "$REGISTRY/$APP_NAME:latest" \
    .

# Push to local registry
echo "📤 Pushing to local registry..."
docker push "$REGISTRY/$APP_NAME:$TAG"
docker push "$REGISTRY/$APP_NAME:$BUILD_ID"
docker push "$REGISTRY/$APP_NAME:latest"

echo "✅ Build and push complete!"
echo ""
echo "Images pushed:"
echo "  - $REGISTRY/$APP_NAME:$TAG"
echo "  - $REGISTRY/$APP_NAME:$BUILD_ID"
echo "  - $REGISTRY/$APP_NAME:latest"
echo ""
echo "To deploy to Kubernetes, update the deployment with:"
echo "  kubectl set image deployment/finance-app app=$REGISTRY/$APP_NAME:$TAG -n production"