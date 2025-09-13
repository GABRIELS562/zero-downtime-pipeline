#!/bin/bash

# Test Dashboard Connectivity to Backend Services
# Tests that the dashboard can connect to Pharma (30002) and Trading (30003) services

echo "🔍 Testing Dashboard Backend Connections"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test Pharma service (Port 30002)
echo -e "${YELLOW}Testing Pharma Management System (Port 30002)...${NC}"
echo "----------------------------------------"

echo "1. Testing main endpoint:"
if curl -s http://localhost:30002/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Pharma main endpoint is accessible${NC}"
    curl -s http://localhost:30002/ | python3 -m json.tool | head -10
else
    echo -e "${RED}❌ Cannot reach Pharma service on port 30002${NC}"
fi

echo ""
echo "2. Testing health endpoint:"
if curl -s http://localhost:30002/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Pharma health endpoint is working${NC}"
    curl -s http://localhost:30002/health/live | python3 -m json.tool
else
    echo -e "${RED}❌ Pharma health endpoint not responding${NC}"
fi

echo ""
echo "3. Testing API endpoints:"
if curl -s http://localhost:30002/api/v1/batches > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Pharma API endpoints are accessible${NC}"
else
    echo -e "${RED}❌ Pharma API endpoints not working${NC}"
fi

# Test Trading service (Port 30003)
echo ""
echo -e "${YELLOW}Testing Trading Platform (Port 30003)...${NC}"
echo "----------------------------------------"

echo "1. Testing main endpoint:"
if curl -s http://localhost:30003/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Trading main endpoint is accessible${NC}"
    curl -s http://localhost:30003/ | python3 -m json.tool | head -10
else
    echo -e "${RED}❌ Cannot reach Trading service on port 30003${NC}"
fi

echo ""
echo "2. Testing health endpoint:"
if curl -s http://localhost:30003/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Trading health endpoint is working${NC}"
    curl -s http://localhost:30003/health/live | python3 -m json.tool
else
    echo -e "${RED}❌ Trading health endpoint not responding${NC}"
fi

echo ""
echo "3. Testing API endpoints:"
if curl -s http://localhost:30003/api/v1/market > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Trading API endpoints are accessible${NC}"
else
    echo -e "${RED}❌ Trading API endpoints not working${NC}"
fi

# Summary
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}DASHBOARD CONNECTION REQUIREMENTS:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "For the dashboard to work properly, ensure:"
echo ""
echo "1. Pharma service is running on port 30002"
echo "   - Health check: http://localhost:30002/health/live"
echo "   - API: http://localhost:30002/api/v1/batches"
echo ""
echo "2. Trading service is running on port 30003"
echo "   - Health check: http://localhost:30003/health/live"
echo "   - API: http://localhost:30003/api/v1/market"
echo ""
echo "3. Dashboard is served with CORS enabled"
echo "   - The Flask apps have CORS enabled via flask-cors"
echo ""
echo "4. To start the services locally:"
echo "   docker run -d -p 30002:8000 localhost:5000/pharma-app:production"
echo "   docker run -d -p 30003:8000 localhost:5000/finance-app:production"
echo ""
echo "5. To serve the dashboard:"
echo "   cd frontend && python3 -m http.server 30004"
echo "   Then access: http://localhost:30004"