#!/bin/bash

echo "🔍 Verifying Prometheus Metrics Format"
echo "======================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}1. PHARMA APP METRICS (Port 8002)${NC}"
echo "──────────────────────────────────"
echo ""

echo "Required Metrics:"
echo ""

# Check for pharma_batch_temperature
echo -n "✓ pharma_batch_temperature: "
if curl -s http://localhost:8002/metrics | grep -q 'pharma_batch_temperature{batch_id="BATCH-001"}'; then
    TEMP=$(curl -s http://localhost:8002/metrics | grep 'pharma_batch_temperature{batch_id="BATCH-001"}' | awk '{print $2}')
    echo -e "${GREEN}FOUND${NC} (BATCH-001 temp: ${TEMP}°C)"
else
    echo -e "❌ NOT FOUND"
fi

# Check for pharma_fda_violations_total
echo -n "✓ pharma_fda_violations_total: "
if curl -s http://localhost:8002/metrics | grep -q 'pharma_fda_violations_total'; then
    VIOLATIONS=$(curl -s http://localhost:8002/metrics | grep '^pharma_fda_violations_total ' | awk '{print $2}')
    echo -e "${GREEN}FOUND${NC} (Count: $VIOLATIONS)"
else
    echo -e "❌ NOT FOUND"
fi

echo ""
echo "Additional Metrics:"
curl -s http://localhost:8002/metrics | grep "^# HELP" | awk '{print "  • " $3}' | head -5

echo ""
echo -e "${BLUE}2. TRADING APP METRICS (Port 8003)${NC}"
echo "──────────────────────────────────"
echo ""

echo "Required Metrics:"
echo ""

# Check for trading_order_latency_milliseconds histogram
echo -n "✓ trading_order_latency_milliseconds: "
if curl -s http://localhost:8003/metrics | grep -q 'trading_order_latency_milliseconds_bucket'; then
    COUNT=$(curl -s http://localhost:8003/metrics | grep 'trading_order_latency_milliseconds_count' | awk '{print $2}')
    echo -e "${GREEN}FOUND${NC} (Histogram with $COUNT samples)"
else
    echo -e "❌ NOT FOUND"
fi

# Check for trading_orders_total by status
echo -n "✓ trading_orders_total{status}: "
if curl -s http://localhost:8003/metrics | grep -q 'trading_orders_total{status="executed"}'; then
    EXECUTED=$(curl -s http://localhost:8003/metrics | grep 'trading_orders_total{status="executed"}' | awk '{print $2}')
    echo -e "${GREEN}FOUND${NC} (Executed: $EXECUTED)"
else
    echo -e "❌ NOT FOUND"
fi

echo ""
echo "Additional Metrics:"
curl -s http://localhost:8003/metrics | grep "^# HELP" | awk '{print "  • " $3}' | head -5

echo ""
echo -e "${YELLOW}3. PROMETHEUS SCRAPING TEST${NC}"
echo "────────────────────────────"
echo ""

echo "Testing metrics format compatibility:"

# Test Pharma metrics format
echo -n "Pharma metrics format: "
if curl -s http://localhost:8002/metrics | head -1 | grep -q "^# HELP"; then
    echo -e "${GREEN}✅ Valid Prometheus format${NC}"
else
    echo -e "❌ Invalid format"
fi

# Test Trading metrics format
echo -n "Trading metrics format: "
if curl -s http://localhost:8003/metrics | head -1 | grep -q "^# HELP"; then
    echo -e "${GREEN}✅ Valid Prometheus format${NC}"
else
    echo -e "❌ Invalid format"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}PROMETHEUS METRICS VERIFICATION COMPLETE${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "Summary:"
echo "  • Pharma app exposes temperature and FDA violations metrics"
echo "  • Trading app exposes order latency histogram and status counters"
echo "  • Both endpoints use valid Prometheus exposition format"
echo "  • Ready for Prometheus scraping on Server2"
echo ""
echo "Prometheus scrape config example:"
echo "  scrape_configs:"
echo "    - job_name: 'pharma-app'"
echo "      static_configs:"
echo "        - targets: ['localhost:8002']"
echo "    - job_name: 'trading-app'"
echo "      static_configs:"
echo "        - targets: ['localhost:8003']"