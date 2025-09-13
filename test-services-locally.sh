#!/bin/bash

# Test both services locally with Docker before Kubernetes deployment

set -e

echo "🧪 Testing Services Locally with Docker"
echo "======================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Build images
echo "Building images..."
cd apps/pharma-manufacturing
docker build -f Dockerfile.flask -t pharma-test:latest . >/dev/null 2>&1
cd ../finance-trading
docker build -f Dockerfile.flask -t trading-test:latest . >/dev/null 2>&1
cd ../..

# Stop any existing test containers
docker stop pharma-test trading-test 2>/dev/null || true
docker rm pharma-test trading-test 2>/dev/null || true

# Run Pharma app
echo ""
echo -e "${GREEN}Starting Pharma Management System on port 30002...${NC}"
docker run -d --name pharma-test -p 30002:8000 pharma-test:latest

# Run Trading app
echo -e "${GREEN}Starting Trading Platform on port 30003...${NC}"
docker run -d --name trading-test -p 30003:8000 trading-test:latest

# Wait for services to start
echo ""
echo "Waiting for services to start..."
sleep 5

# Test Pharma app
echo ""
echo -e "${YELLOW}Testing Pharma Management System (port 30002)...${NC}"
echo "================================================"

if curl -s http://localhost:30002/ | python3 -m json.tool | head -15; then
    echo -e "${GREEN}✅ Pharma app is working${NC}"
else
    echo -e "${RED}❌ Pharma app test failed${NC}"
fi

echo ""
echo "Health check:"
curl -s http://localhost:30002/health/live | python3 -m json.tool

# Test Trading app
echo ""
echo -e "${YELLOW}Testing Trading Platform (port 30003)...${NC}"
echo "========================================="

if curl -s http://localhost:30003/ | python3 -m json.tool | head -15; then
    echo -e "${GREEN}✅ Trading app is working${NC}"
else
    echo -e "${RED}❌ Trading app test failed${NC}"
fi

echo ""
echo "Health check:"
curl -s http://localhost:30003/health/live | python3 -m json.tool

# Show available endpoints
echo ""
echo -e "${GREEN}Available Endpoints:${NC}"
echo "===================="
echo ""
echo "Pharma Management System (http://localhost:30002):"
echo "  • /                      - Main endpoint"
echo "  • /health/live           - Health check"
echo "  • /api/v1/batches        - Batch information"
echo "  • /api/v1/equipment      - Equipment status"
echo "  • /api/v1/quality        - Quality control"
echo "  • /metrics               - Prometheus metrics"
echo ""
echo "Trading Platform (http://localhost:30003):"
echo "  • /                      - Main endpoint"
echo "  • /health/live           - Health check"
echo "  • /api/v1/market         - Market data"
echo "  • /api/v1/orders         - Order management"
echo "  • /api/v1/portfolio      - Portfolio view"
echo "  • /metrics               - Prometheus metrics"
echo ""
echo -e "${YELLOW}Test containers are running. To stop them:${NC}"
echo "  docker stop pharma-test trading-test"
echo "  docker rm pharma-test trading-test"
echo ""
echo -e "${GREEN}✅ Local testing complete!${NC}"