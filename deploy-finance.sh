#!/bin/bash

# Deploy Finance Trading App to Kubernetes
# This script handles the complete deployment process

set -e

echo "💹 Deploying Finance Trading System"
echo "===================================="
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

# Step 2: Build and push Docker image
echo ""
echo "🔨 Step 2: Building and pushing Finance app Docker image..."
cd apps/finance-trading

# Check if local registry is running
if ! curl -s http://localhost:5000/v2/_catalog &>/dev/null; then
    echo "  ⚠️  Warning: Local registry at localhost:5000 might not be running"
    echo "  Starting a local registry..."
    docker run -d -p 5000:5000 --name registry --restart=always registry:2 2>/dev/null || echo "  Registry already exists"
    sleep 3
fi

# Build and push the image (with fallback support)
if [ -f "./build-with-fallback.sh" ]; then
    echo "  Using build-with-fallback.sh..."
    ./build-with-fallback.sh production
elif [ -f "./build-and-push.sh" ]; then
    echo "  Using build-and-push.sh..."
    ./build-and-push.sh production
else
    echo "  Building directly with Docker..."
    # Try main Dockerfile first
    if docker build --target production -t localhost:5000/finance-app:production . ; then
        echo "  ✅ Main build successful"
    else
        echo "  ⚠️  Main build failed, trying fallback..."
        docker build -f Dockerfile.fallback -t localhost:5000/finance-app:production .
    fi
    docker push localhost:5000/finance-app:production
fi

cd ../..

# Step 3: Deploy Finance application
echo ""
echo "🚀 Step 3: Deploying Finance application..."
kubectl apply -f k8s-manifests/finance-app-deployment.yaml

# Step 4: Wait for deployment to be ready
echo ""
echo "⏳ Step 4: Waiting for Finance app to be ready..."
kubectl rollout status deployment/finance-app -n production --timeout=120s

# Step 5: Display deployment status
echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n production -l app=finance-app
echo ""

# Step 6: Display access information
echo "🌐 Access Information:"
echo "====================="
echo ""
echo "Internal Service (ClusterIP): finance-app.production.svc.cluster.local:8000"
echo "NodePort Access: http://localhost:30003"
echo "Dashboard Access: http://dashboard.jagdevops.co.za (if configured)"
echo ""
echo "Health Endpoints:"
echo "  - Live:  http://localhost:30003/health/live"
echo "  - Ready: http://localhost:30003/health/ready"
echo "  - Main:  http://localhost:30003/"
echo ""

# Step 7: Test the deployment
echo "🧪 Testing deployment..."
if curl -s http://localhost:30003/health/live &>/dev/null; then
    echo "✅ Health check passed - Application is running!"
    echo ""
    echo "Sample response from health endpoint:"
    curl -s http://localhost:30003/health/live | head -1
elif curl -s http://localhost:30003/ &>/dev/null; then
    echo "✅ Application is responding (fallback mode)"
else
    echo "⚠️  Health check failed - Application might still be starting up"
    echo "  Try checking manually:"
    echo "    curl http://localhost:30003/health/live"
    echo "    curl http://localhost:30003/"
fi

echo ""
echo "📝 Useful Commands:"
echo "=================="
echo "View logs:        kubectl logs -f deployment/finance-app -n production"
echo "Restart app:      kubectl rollout restart deployment/finance-app -n production"
echo "Scale replicas:   kubectl scale deployment/finance-app --replicas=3 -n production"
echo "Port forward:     kubectl port-forward -n production svc/finance-app 8000:8000"
echo "Delete deployment: kubectl delete -f k8s-manifests/finance-app-deployment.yaml"
echo ""
echo "💹 Finance Trading System deployment complete!"
echo ""
echo "Note: The app is accessible through the dashboard at dashboard.jagdevops.co.za"
echo "      and directly via NodePort at http://localhost:30003"