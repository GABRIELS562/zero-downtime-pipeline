#!/bin/bash

echo "🚀 Deploying Complete System with Docker Compose"
echo "================================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Stop existing containers
echo "Stopping existing containers..."
docker stop pharma-app trading-app dashboard 2>/dev/null
docker rm pharma-app trading-app dashboard 2>/dev/null

echo ""
echo -e "${YELLOW}Building and starting services...${NC}"
echo ""

# Build and start with docker-compose
docker-compose up -d --build

echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo -e "${BLUE}Service Status:${NC}"
echo "─────────────"

# Check Pharma
PHARMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health/live)
if [ "$PHARMA_STATUS" == "200" ]; then
    echo -e "Pharma App (8002): ${GREEN}✅ RUNNING${NC}"
else
    echo -e "Pharma App (8002): ❌ NOT RESPONDING"
fi

# Check Trading
TRADING_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/health/live)
if [ "$TRADING_STATUS" == "200" ]; then
    echo -e "Trading App (8003): ${GREEN}✅ RUNNING${NC}"
else
    echo -e "Trading App (8003): ❌ NOT RESPONDING"
fi

# Check Dashboard
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8004/index-landing.html)
if [ "$DASHBOARD_STATUS" == "200" ]; then
    echo -e "Dashboard (8004): ${GREEN}✅ RUNNING${NC}"
else
    echo -e "Dashboard (8004): ❌ NOT RESPONDING"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "Access points:"
echo "  • Main Hub: http://localhost:8004/index-landing.html"
echo "  • Trading Dashboard: http://localhost:8004/index.html"
echo "  • Pharma Dashboard: http://localhost:8004/pharma-dashboard.html"
echo "  • Pharma API: http://localhost:8002"
echo "  • Trading API: http://localhost:8003"
echo ""
echo "Docker Compose Commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop all: docker-compose down"
echo "  • Restart: docker-compose restart"
echo "  • Scale: docker-compose up -d --scale pharma-app=2"