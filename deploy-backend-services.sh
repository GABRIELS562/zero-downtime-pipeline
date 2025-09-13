#!/bin/bash

# Complete deployment script for backend services
# Deploys Pharma and Trading apps to Kubernetes

set -e

echo "🚀 Deploying Backend Services to Kubernetes"
echo "==========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check command success
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

# Step 1: Build and push images
echo -e "${YELLOW}Step 1: Building and pushing Docker images...${NC}"
./build-and-deploy-services.sh
check_status "Docker build and push"

# Step 2: Create namespace if needed
echo ""
echo -e "${YELLOW}Step 2: Ensuring production namespace exists...${NC}"
kubectl create namespace production 2>/dev/null || echo "Namespace already exists"

# Step 3: Deploy PostgreSQL (if needed for Pharma)
echo ""
echo -e "${YELLOW}Step 3: Deploying PostgreSQL database...${NC}"
if [ -f "k8s-manifests/postgresql-deployment.yaml" ]; then
    kubectl apply -f k8s-manifests/postgresql-deployment.yaml
    check_status "PostgreSQL deployment"
    echo "Waiting for PostgreSQL to be ready..."
    sleep 10
else
    echo "PostgreSQL deployment file not found, skipping..."
fi

# Step 4: Deploy Pharma app
echo ""
echo -e "${YELLOW}Step 4: Deploying Pharma Management System...${NC}"
kubectl apply -f k8s-manifests/pharma-app-deployment.yaml
check_status "Pharma app deployment"

# Step 5: Deploy Finance app
echo ""
echo -e "${YELLOW}Step 5: Deploying Trading Platform...${NC}"
kubectl apply -f k8s-manifests/finance-app-deployment.yaml
check_status "Finance app deployment"

# Step 6: Restart deployments to ensure latest images
echo ""
echo -e "${YELLOW}Step 6: Restarting deployments to pull latest images...${NC}"
kubectl rollout restart deployment pharma-app -n production
kubectl rollout restart deployment finance-app -n production
check_status "Deployment restart"

# Step 7: Wait for rollout
echo ""
echo -e "${YELLOW}Step 7: Waiting for deployments to be ready...${NC}"
kubectl rollout status deployment pharma-app -n production --timeout=120s &
kubectl rollout status deployment finance-app -n production --timeout=120s &
wait
check_status "Deployment rollout"

# Step 8: Check pod status
echo ""
echo -e "${YELLOW}Step 8: Checking pod status...${NC}"
kubectl get pods -n production

# Step 9: Check services
echo ""
echo -e "${YELLOW}Step 9: Checking services...${NC}"
kubectl get svc -n production

# Step 10: Test endpoints (if cluster is accessible)
echo ""
echo -e "${YELLOW}Step 10: Service Information...${NC}"
echo "======================================"
echo ""
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo ""
echo "Services are available at:"
echo "  • Pharma Management System: http://localhost:30002"
echo "  • Trading Platform: http://localhost:30003"
echo "  • Dashboard: http://dashboard.jagdevops.co.za (port 30004)"
echo ""
echo "Health check endpoints:"
echo "  • Pharma: http://localhost:30002/health/live"
echo "  • Trading: http://localhost:30003/health/live"
echo ""
echo "API Documentation:"
echo "  • Pharma: http://localhost:30002/"
echo "  • Trading: http://localhost:30003/"
echo ""
echo "Useful commands:"
echo "  • View logs: kubectl logs -f deployment/pharma-app -n production"
echo "  • View logs: kubectl logs -f deployment/finance-app -n production"
echo "  • Get pods: kubectl get pods -n production"
echo "  • Describe pod: kubectl describe pod <pod-name> -n production"
echo ""
echo "To test the services:"
echo "  curl http://localhost:30002/health/live"
echo "  curl http://localhost:30003/health/live"