#!/bin/bash

# Build Finance Trading app with fallback option
# Tries main Dockerfile first, falls back to simple version if build fails

set -e

# Configuration
REGISTRY="localhost:5000"
APP_NAME="finance-app"
TAG="${1:-production}"
BUILD_ID=$(date +%Y%m%d-%H%M%S)
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "💹 Building Finance Trading Application"
echo "========================================="
echo "Registry: $REGISTRY"
echo "Tag: $TAG"
echo "Build ID: $BUILD_ID"
echo ""

# Check if local registry is running
if ! curl -s http://localhost:5000/v2/_catalog &>/dev/null; then
    echo "⚠️  Local registry at localhost:5000 might not be running"
    echo "Starting a local registry..."
    docker run -d -p 5000:5000 --name registry --restart=always registry:2 2>/dev/null || echo "Registry already exists"
    sleep 3
fi

# Try building with main Dockerfile
echo "📦 Attempting to build with main Dockerfile..."
if docker build \
    --target production \
    --build-arg BUILD_ID="$BUILD_ID" \
    --build-arg GIT_COMMIT="$GIT_COMMIT" \
    --build-arg BUILD_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    -t "$REGISTRY/$APP_NAME:$TAG" \
    -t "$REGISTRY/$APP_NAME:$BUILD_ID" \
    -t "$REGISTRY/$APP_NAME:latest" \
    . 2>&1 | tee /tmp/docker-build.log; then

    echo "✅ Main build successful!"

else
    echo "⚠️  Main build failed, using fallback Dockerfile..."

    # Build with fallback
    if docker build \
        -f Dockerfile.fallback \
        -t "$REGISTRY/$APP_NAME:$TAG" \
        -t "$REGISTRY/$APP_NAME:$BUILD_ID" \
        -t "$REGISTRY/$APP_NAME:latest" \
        . ; then

        echo "✅ Fallback build successful!"
    else
        echo "❌ Both builds failed. Please check the error messages above."
        exit 1
    fi
fi

# Push to local registry
echo ""
echo "📤 Pushing to local registry..."
docker push "$REGISTRY/$APP_NAME:$TAG"
docker push "$REGISTRY/$APP_NAME:$BUILD_ID"
docker push "$REGISTRY/$APP_NAME:latest"

echo ""
echo "✅ Build and push complete!"
echo ""
echo "Images pushed:"
echo "  - $REGISTRY/$APP_NAME:$TAG"
echo "  - $REGISTRY/$APP_NAME:$BUILD_ID"
echo "  - $REGISTRY/$APP_NAME:latest"
echo ""
echo "To deploy to Kubernetes:"
echo "  kubectl apply -f ../../k8s-manifests/finance-app-deployment.yaml"