#!/bin/bash

# Deploy All Applications (Pharma & Finance) to Kubernetes
# This script handles the complete deployment of both applications

set -e

echo "🚀 Deploying All Applications to Kubernetes"
echo "==========================================="
echo ""

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
    echo "❌ Error: kubectl is not configured or cluster is not accessible"
    echo "Please ensure Kubernetes cluster is running and kubectl is configured"
    exit 1
fi

# Ensure local registry is running
echo "🐳 Ensuring Docker registry is running..."
if ! curl -s http://localhost:5000/v2/_catalog &>/dev/null; then
    echo "Starting local registry at localhost:5000..."
    docker run -d -p 5000:5000 --name registry --restart=always registry:2 2>/dev/null || echo "Registry already exists"
    sleep 3
fi

# Deploy Pharma app
echo ""
echo "================== PHARMA APP =================="
if [ -f "./deploy-pharma.sh" ]; then
    ./deploy-pharma.sh
else
    echo "⚠️  deploy-pharma.sh not found, skipping Pharma deployment"
fi

# Deploy Finance app
echo ""
echo "================== FINANCE APP =================="
if [ -f "./deploy-finance.sh" ]; then
    ./deploy-finance.sh
else
    echo "⚠️  deploy-finance.sh not found, skipping Finance deployment"
fi

# Summary
echo ""
echo "========================================="
echo "📊 DEPLOYMENT SUMMARY"
echo "========================================="
echo ""

echo "Pharma Manufacturing App:"
echo "  - NodePort: http://localhost:30002"
echo "  - Health: http://localhost:30002/api/v1/health/live"
echo ""

echo "Finance Trading App:"
echo "  - NodePort: http://localhost:30003"
echo "  - Health: http://localhost:30003/health/live"
echo "  - Dashboard: http://dashboard.jagdevops.co.za"
echo ""

echo "All Pods in Production namespace:"
kubectl get pods -n production
echo ""

echo "All Services in Production namespace:"
kubectl get svc -n production
echo ""

echo "✅ All applications deployed successfully!"
echo ""
echo "📝 Quick Commands:"
echo "  View all logs:     kubectl logs -n production -l tier=backend --tail=50"
echo "  Restart all apps:  kubectl rollout restart deployment -n production"
echo "  Check health:      curl http://localhost:30002/api/v1/health/live && curl http://localhost:30003/health/live"