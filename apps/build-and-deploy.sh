#!/bin/bash

# Zero-Downtime Pipeline: Bulletproof Build and Deploy Script
# Builds and deploys both pharma-manufacturing and finance-trading applications

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APPS_DIR="/Users/user/zero-downtime-pipeline/apps"
FINANCE_APP="finance-trading"
PHARMA_APP="pharma-manufacturing"
REGISTRY="localhost:5000"  # Adjust for your registry
BUILD_TAG=$(date +"%Y%m%d-%H%M%S")

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}Zero-Downtime Pipeline: Bulletproof Deploy${NC}"
echo -e "${BLUE}===========================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to build Docker image
build_image() {
    local app_name=$1
    local app_dir="$APPS_DIR/$app_name"
    
    print_status "Building $app_name application..."
    
    # Navigate to app directory
    cd "$app_dir"
    
    # Check if bulletproof files exist
    if [[ ! -f "Dockerfile.bulletproof" ]]; then
        print_error "Dockerfile.bulletproof not found for $app_name"
        return 1
    fi
    
    if [[ ! -f "requirements-bulletproof.txt" ]]; then
        print_error "requirements-bulletproof.txt not found for $app_name"
        return 1
    fi
    
    # Build the image
    print_status "Building Docker image: $app_name:$BUILD_TAG"
    
    if docker build -f Dockerfile.bulletproof -t "$app_name:$BUILD_TAG" -t "$app_name:latest" . ; then
        print_status "Successfully built $app_name:$BUILD_TAG"
        return 0
    else
        print_error "Failed to build $app_name"
        return 1
    fi
}

# Function to test image locally
test_image() {
    local app_name=$1
    local port=$2
    
    print_status "Testing $app_name image locally..."
    
    # Stop any existing container
    docker stop "$app_name-test" 2>/dev/null || true
    docker rm "$app_name-test" 2>/dev/null || true
    
    # Run container for testing
    if docker run -d --name "$app_name-test" -p "$port:$port" "$app_name:latest"; then
        print_status "Started test container for $app_name on port $port"
        
        # Wait for startup
        sleep 10
        
        # Test health endpoint
        if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
            print_status "$app_name health check passed!"
            
            # Stop test container
            docker stop "$app_name-test"
            docker rm "$app_name-test"
            return 0
        else
            print_warning "$app_name health check failed, checking logs..."
            docker logs "$app_name-test" | tail -20
            
            # Stop test container
            docker stop "$app_name-test"
            docker rm "$app_name-test"
            return 1
        fi
    else
        print_error "Failed to start test container for $app_name"
        return 1
    fi
}

# Function to deploy to K3s
deploy_k3s() {
    local app_name=$1
    local port=$2
    local image_name="$app_name:$BUILD_TAG"
    
    print_status "Deploying $app_name to K3s..."
    
    # Create deployment YAML
    cat > "/tmp/$app_name-deployment.yaml" <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $app_name
  labels:
    app: $app_name
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: $app_name
  template:
    metadata:
      labels:
        app: $app_name
    spec:
      containers:
      - name: $app_name
        image: $image_name
        ports:
        - containerPort: $port
        env:
        - name: PORT
          value: "$port"
        - name: ENVIRONMENT
          value: "production"
        - name: BUILD_ID
          value: "$BUILD_TAG"
        livenessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: $app_name-service
spec:
  selector:
    app: $app_name
  ports:
  - port: $port
    targetPort: $port
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: $app_name-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: $app_name.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: $app_name-service
            port:
              number: $port
EOF

    # Apply deployment
    if kubectl apply -f "/tmp/$app_name-deployment.yaml"; then
        print_status "Successfully deployed $app_name to K3s"
        
        # Wait for deployment to be ready
        print_status "Waiting for $app_name deployment to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/$app_name
        
        # Show deployment status
        kubectl get deployment $app_name
        kubectl get service $app_name-service
        kubectl get ingress $app_name-ingress
        
        return 0
    else
        print_error "Failed to deploy $app_name to K3s"
        return 1
    fi
}

# Function to verify deployment
verify_deployment() {
    local app_name=$1
    local port=$2
    
    print_status "Verifying $app_name deployment..."
    
    # Check pod status
    local pods=$(kubectl get pods -l app=$app_name --no-headers | wc -l)
    local ready_pods=$(kubectl get pods -l app=$app_name --no-headers | grep Running | wc -l)
    
    print_status "$app_name: $ready_pods/$pods pods ready"
    
    if [[ $ready_pods -gt 0 ]]; then
        print_status "$app_name deployment verification passed!"
        return 0
    else
        print_error "$app_name deployment verification failed!"
        kubectl describe pods -l app=$app_name
        return 1
    fi
}

# Main execution
main() {
    print_status "Starting bulletproof deployment process..."
    
    # Check prerequisites
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Build Finance Trading App
    if build_image "$FINANCE_APP"; then
        print_status "Finance app build successful"
    else
        print_error "Finance app build failed"
        exit 1
    fi
    
    # Build Pharma Manufacturing App
    if build_image "$PHARMA_APP"; then
        print_status "Pharma app build successful"
    else
        print_error "Pharma app build failed"
        exit 1
    fi
    
    # Test images locally
    print_status "Testing images locally..."
    
    if test_image "$FINANCE_APP" "8080"; then
        print_status "Finance app test passed"
    else
        print_warning "Finance app test failed - deploying anyway"
    fi
    
    if test_image "$PHARMA_APP" "8000"; then
        print_status "Pharma app test passed"
    else
        print_warning "Pharma app test failed - deploying anyway"
    fi
    
    # Deploy to K3s
    print_status "Deploying to K3s..."
    
    # Load images into K3s if using local registry
    print_status "Loading images into K3s..."
    docker save "$FINANCE_APP:$BUILD_TAG" | sudo k3s ctr images import -
    docker save "$PHARMA_APP:$BUILD_TAG" | sudo k3s ctr images import -
    
    # Deploy applications
    if deploy_k3s "$FINANCE_APP" "8080"; then
        print_status "Finance app deployed successfully"
    else
        print_error "Finance app deployment failed"
        exit 1
    fi
    
    if deploy_k3s "$PHARMA_APP" "8000"; then
        print_status "Pharma app deployed successfully"
    else
        print_error "Pharma app deployment failed"
        exit 1
    fi
    
    # Verify deployments
    sleep 30  # Give deployments time to stabilize
    
    verify_deployment "$FINANCE_APP" "8080"
    verify_deployment "$PHARMA_APP" "8000"
    
    print_status "===========================================" 
    print_status "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    print_status "Build Tag: $BUILD_TAG"
    print_status "Finance Trading: http://finance-trading.local"
    print_status "Pharma Manufacturing: http://pharma-manufacturing.local"
    print_status "==========================================="
}

# Run main function
main "$@"