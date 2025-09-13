#!/bin/bash

# Build and Deploy Both Backend Services
# Pharma app on port 30002 and Trading app on port 30003

set -e

echo "🚀 Building and Deploying Backend Services"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info &>/dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Ensure local registry is running
echo "🐳 Ensuring Docker registry is running..."
if ! curl -s http://localhost:5000/v2/_catalog &>/dev/null; then
    echo "Starting local registry at localhost:5000..."
    docker run -d -p 5000:5000 --name registry --restart=always registry:2 2>/dev/null || echo "Registry already running"
    sleep 3
fi

# Build and push Pharma app
echo ""
echo -e "${GREEN}=============== BUILDING PHARMA APP ===============${NC}"
echo "Building Pharma Management System..."
cd apps/pharma-manufacturing

# Try to build with Flask app
echo "Building Flask-based Pharma app..."
docker build -f Dockerfile.flask -t localhost:5000/pharma-app:production -t localhost:5000/pharma-app:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Pharma app built successfully${NC}"
    echo "Pushing to registry..."
    docker push localhost:5000/pharma-app:production
    docker push localhost:5000/pharma-app:latest
else
    echo -e "${RED}❌ Pharma app build failed${NC}"
    exit 1
fi

cd ../..

# Build and push Trading app
echo ""
echo -e "${GREEN}=============== BUILDING TRADING APP ===============${NC}"
echo "Building Trading Platform..."
cd apps/finance-trading

# Try to build with Flask app
echo "Building Flask-based Trading app..."
docker build -f Dockerfile.flask -t localhost:5000/finance-app:production -t localhost:5000/finance-app:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Trading app built successfully${NC}"
    echo "Pushing to registry..."
    docker push localhost:5000/finance-app:production
    docker push localhost:5000/finance-app:latest
else
    echo -e "${RED}❌ Trading app build failed${NC}"
    exit 1
fi

cd ../..

# Summary
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✅ BUILD COMPLETE${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Images built and pushed:"
echo "  • localhost:5000/pharma-app:production"
echo "  • localhost:5000/finance-app:production"
echo ""
echo "To deploy to Kubernetes, run:"
echo "  kubectl apply -f k8s-manifests/postgresql-deployment.yaml"
echo "  kubectl apply -f k8s-manifests/pharma-app-deployment.yaml"
echo "  kubectl apply -f k8s-manifests/finance-app-deployment.yaml"
echo ""
echo "Then restart the deployments:"
echo "  kubectl rollout restart deployment pharma-app -n production"
echo "  kubectl rollout restart deployment finance-app -n production"
echo ""
echo "Access the services at:"
echo "  • Pharma: http://localhost:30002"
echo "  • Trading: http://localhost:30003"
echo "  • Dashboard: http://dashboard.jagdevops.co.za (port 30004)"