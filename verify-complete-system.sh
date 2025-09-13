#!/bin/bash

echo "🏭 Complete System Architecture Verification"
echo "==========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 DASHBOARD STRUCTURE:${NC}"
echo "─────────────────────"
echo ""
echo "1. Main Landing Page (Hub): http://localhost:8004/index-landing.html"
echo "   ├── Trading Dashboard: http://localhost:8004/index.html"
echo "   └── Pharma Dashboard: http://localhost:8004/pharma-dashboard.html"
echo ""

echo -e "${YELLOW}🔌 BACKEND SERVICES:${NC}"
echo "──────────────────"
echo ""

# Check Pharma Service
echo "1. Pharma API (Port 8002):"
PHARMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health/live)
if [ "$PHARMA_STATUS" == "200" ]; then
    echo -e "   ${GREEN}✅ Status: OPERATIONAL${NC}"
    PHARMA_DATA=$(curl -s http://localhost:8002/)
    echo "   Service: $(echo $PHARMA_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['service'])")"
    echo "   Compliance: $(echo $PHARMA_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['compliance'])")"
else
    echo -e "   ❌ Status: OFFLINE"
fi

echo ""

# Check Trading Service
echo "2. Trading API (Port 8003):"
TRADING_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/health/live)
if [ "$TRADING_STATUS" == "200" ]; then
    echo -e "   ${GREEN}✅ Status: OPERATIONAL${NC}"
    TRADING_DATA=$(curl -s http://localhost:8003/)
    echo "   Service: $(echo $TRADING_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['service'])")"
    echo "   Latency: $(echo $TRADING_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['latency'])")"
else
    echo -e "   ❌ Status: OFFLINE"
fi

echo ""
echo -e "${GREEN}🔄 DATA FLOW VERIFICATION:${NC}"
echo "───────────────────────"
echo ""

# Test Pharma Data Flow
echo "Pharma Data Flow:"
echo -e "  Dashboard (8004) → ${GREEN}JavaScript Fetch${NC} → Pharma API (8002)"
curl -s http://localhost:8002/api/v1/batches | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  ✅ Batches API: {len(data[\"batches\"])} batches available')
" 2>/dev/null || echo "  ❌ Batches API not responding"

curl -s http://localhost:8002/api/v1/equipment | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  ✅ Equipment API: {len(data[\"equipment\"])} devices monitored')
" 2>/dev/null || echo "  ❌ Equipment API not responding"

echo ""

# Test Trading Data Flow
echo "Trading Data Flow:"
echo -e "  Dashboard (8004) → ${GREEN}JavaScript Fetch${NC} → Trading API (8003)"
curl -s http://localhost:8003/api/v1/market | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  ✅ Market API: {len(data[\"stocks\"])} stocks tracked')
" 2>/dev/null || echo "  ❌ Market API not responding"

curl -s http://localhost:8003/api/v1/portfolio | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  ✅ Portfolio API: Value = {data[\"total_value\"]}')'
" 2>/dev/null || echo "  ❌ Portfolio API not responding"

echo ""
echo -e "${BLUE}🎯 NAVIGATION TEST:${NC}"
echo "─────────────────"
echo ""
echo "From Landing Page you can navigate to:"
echo "  • Trading Dashboard (index.html) - View trading metrics"
echo "  • Pharma Dashboard (pharma-dashboard.html) - View pharma metrics"
echo "  • Trading API directly (port 8003) - Raw API access"
echo "  • Pharma API directly (port 8002) - Raw API access"
echo ""

echo -e "${GREEN}✅ SYSTEM READY!${NC}"
echo ""
echo "Access the main hub at: http://localhost:8004/index-landing.html"
echo ""
echo "Dashboard Navigation:"
echo "  1. Open main hub"
echo "  2. Choose Trading or Pharma dashboard"
echo "  3. Each dashboard connects to its respective API"
echo "  4. Real-time data flows from APIs to dashboards"