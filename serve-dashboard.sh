#!/bin/bash

# Serve the Dashboard on Port 30004
# Connects to Pharma (30002) and Trading (30003) backend services

echo "🌐 Starting Dashboard Server"
echo "============================"
echo ""

# Check if services are running
echo "Checking backend services..."
PHARMA_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:30002/health/live 2>/dev/null)
TRADING_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:30003/health/live 2>/dev/null)

if [ "$PHARMA_CHECK" == "200" ]; then
    echo "✅ Pharma service is running on port 30002"
else
    echo "⚠️  Warning: Pharma service not responding on port 30002"
    echo "   Run: docker run -d -p 30002:8000 localhost:5000/pharma-app:production"
fi

if [ "$TRADING_CHECK" == "200" ]; then
    echo "✅ Trading service is running on port 30003"
else
    echo "⚠️  Warning: Trading service not responding on port 30003"
    echo "   Run: docker run -d -p 30003:8000 localhost:5000/finance-app:production"
fi

echo ""
echo "Starting dashboard server..."
echo "----------------------------"
echo ""
echo "Dashboard will be available at:"
echo "  • http://localhost:30004"
echo "  • http://dashboard.jagdevops.co.za (if DNS configured)"
echo ""
echo "Backend services:"
echo "  • Pharma: http://localhost:30002"
echo "  • Trading: http://localhost:30003"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
cd frontend
python3 -m http.server 30004 --bind 0.0.0.0