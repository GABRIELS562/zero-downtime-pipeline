#!/bin/bash

# Deploy Pharma Manufacturing App to Kubernetes
# This script handles the complete deployment process

set -e

echo "🏭 Deploying Pharmaceutical Manufacturing System"
echo "================================================"
echo ""

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
    echo "❌ Error: kubectl is not configured or cluster is not accessible"
    echo "Please ensure Kubernetes cluster is running and kubectl is configured"
    exit 1
fi

# Step 1: Create production namespace if it doesn't exist
echo "📦 Step 1: Ensuring production namespace exists..."
kubectl create namespace production 2>/dev/null || echo "  Namespace 'production' already exists"

# Step 2: Deploy PostgreSQL database
echo ""
echo "🗄️  Step 2: Deploying PostgreSQL database..."
kubectl apply -f k8s-manifests/postgresql-deployment.yaml
echo "  Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgresql -n production --timeout=60s 2>/dev/null || echo "  PostgreSQL is starting up..."

# Step 3: Build and push Docker image
echo ""
echo "🔨 Step 3: Building and pushing Pharma app Docker image..."
cd apps/pharma-manufacturing

# Check if local registry is running
if ! curl -s http://localhost:5000/v2/_catalog &>/dev/null; then
    echo "  ⚠️  Warning: Local registry at localhost:5000 might not be running"
    echo "  Starting a local registry..."
    docker run -d -p 5000:5000 --name registry --restart=always registry:2 2>/dev/null || echo "  Registry already exists"
    sleep 3
fi

# Build and push the image
./build-and-push.sh production

cd ../..

# Step 4: Deploy Pharma application
echo ""
echo "🚀 Step 4: Deploying Pharma application..."
kubectl apply -f k8s-manifests/pharma-app-deployment.yaml

# Step 5: Wait for deployment to be ready
echo ""
echo "⏳ Step 5: Waiting for Pharma app to be ready..."
kubectl rollout status deployment/pharma-app -n production --timeout=120s

# Step 6: Display deployment status
echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n production -l app=pharma-app
echo ""
kubectl get pods -n production -l app=postgresql
echo ""

# Step 7: Display access information
echo "🌐 Access Information:"
echo "====================="
echo ""
echo "Internal Service (ClusterIP): pharma-app.production.svc.cluster.local:8000"
echo "NodePort Access: http://localhost:30002"
echo ""
echo "Health Endpoints:"
echo "  - Live:  http://localhost:30002/api/v1/health/live"
echo "  - Ready: http://localhost:30002/api/v1/health/ready"
echo "  - API Docs: http://localhost:30002/api/docs"
echo ""

# Step 8: Test the deployment
echo "🧪 Testing deployment..."
if curl -s http://localhost:30002/api/v1/health/live &>/dev/null; then
    echo "✅ Health check passed - Application is running!"
else
    echo "⚠️  Health check failed - Application might still be starting up"
    echo "  Try checking manually: curl http://localhost:30002/api/v1/health/live"
fi

echo ""
echo "📝 Useful Commands:"
echo "=================="
echo "View logs:           kubectl logs -f deployment/pharma-app -n production"
echo "View PostgreSQL logs: kubectl logs -f deployment/postgresql -n production"
echo "Restart app:         kubectl rollout restart deployment/pharma-app -n production"
echo "Scale replicas:      kubectl scale deployment/pharma-app --replicas=3 -n production"
echo "Delete deployment:   kubectl delete -f k8s-manifests/pharma-app-deployment.yaml"
echo ""
echo "🏭 Pharma Manufacturing System deployment complete!"