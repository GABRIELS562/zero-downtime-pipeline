#!/bin/bash

# Zero-Downtime Pipeline: Build Verification Script
# Verifies that both applications can be built and started successfully

set -e

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

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to verify Python dependencies
verify_dependencies() {
    local app_name=$1
    local app_dir="$APPS_DIR/$app_name"
    
    print_status "Verifying dependencies for $app_name..."
    
    cd "$app_dir"
    
    # Check if requirements file exists
    if [[ ! -f "requirements-bulletproof.txt" ]]; then
        print_error "requirements-bulletproof.txt not found for $app_name"
        return 1
    fi
    
    # Create temporary virtual environment
    python3 -m venv "/tmp/venv-$app_name" || {
        print_error "Failed to create virtual environment for $app_name"
        return 1
    }
    
    source "/tmp/venv-$app_name/bin/activate"
    
    # Install dependencies
    pip install --quiet -r requirements-bulletproof.txt || {
        print_error "Failed to install dependencies for $app_name"
        deactivate
        rm -rf "/tmp/venv-$app_name"
        return 1
    }
    
    # Test imports
    if [[ "$app_name" == "$FINANCE_APP" ]]; then
        python -c "
import sys
sys.path.append('/Users/user/zero-downtime-pipeline/apps/finance-trading/src')
try:
    import httpx
    import alpha_vantage
    import pandas
    import numpy
    from fastapi import FastAPI
    import uvicorn
    import prometheus_client
    print('✓ All critical imports successful for finance-trading')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
" || {
            print_error "Import verification failed for $app_name"
            deactivate
            rm -rf "/tmp/venv-$app_name"
            return 1
        }
    elif [[ "$app_name" == "$PHARMA_APP" ]]; then
        python -c "
import sys
sys.path.append('/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src')
try:
    from fastapi import FastAPI
    import uvicorn
    import sqlalchemy
    import pandas
    import numpy
    import prometheus_client
    print('✓ All critical imports successful for pharma-manufacturing')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
" || {
            print_error "Import verification failed for $app_name"
            deactivate
            rm -rf "/tmp/venv-$app_name"
            return 1
        }
    fi
    
    deactivate
    rm -rf "/tmp/venv-$app_name"
    
    print_status "Dependencies verified for $app_name"
    return 0
}

# Function to verify file structure
verify_structure() {
    local app_name=$1
    local app_dir="$APPS_DIR/$app_name"
    
    print_status "Verifying file structure for $app_name..."
    
    # Check critical files exist
    local critical_files=(
        "$app_dir/src/main.py"
        "$app_dir/requirements-bulletproof.txt"
        "$app_dir/Dockerfile.bulletproof"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Missing critical file: $file"
            return 1
        fi
    done
    
    # Check __init__.py files
    local init_files=(
        "$app_dir/src/__init__.py"
        "$app_dir/src/api/__init__.py"
        "$app_dir/src/services/__init__.py"
        "$app_dir/src/middleware/__init__.py"
    )
    
    for file in "${init_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Missing __init__.py file: $file"
            return 1
        fi
    done
    
    print_status "File structure verified for $app_name"
    return 0
}

# Function to build Docker image
test_build() {
    local app_name=$1
    local app_dir="$APPS_DIR/$app_name"
    
    print_status "Testing Docker build for $app_name..."
    
    cd "$app_dir"
    
    # Build the image
    if docker build -f Dockerfile.bulletproof -t "$app_name:test" . >/dev/null 2>&1; then
        print_status "Docker build successful for $app_name"
        
        # Clean up test image
        docker rmi "$app_name:test" >/dev/null 2>&1 || true
        
        return 0
    else
        print_error "Docker build failed for $app_name"
        
        # Show build output for debugging
        print_status "Build output for debugging:"
        docker build -f Dockerfile.bulletproof -t "$app_name:test-debug" . || true
        docker rmi "$app_name:test-debug" >/dev/null 2>&1 || true
        
        return 1
    fi
}

# Function to test container startup
test_startup() {
    local app_name=$1
    local port=$2
    
    print_status "Testing container startup for $app_name..."
    
    # Stop any existing test container
    docker stop "$app_name-startup-test" 2>/dev/null || true
    docker rm "$app_name-startup-test" 2>/dev/null || true
    
    # Build fresh image
    cd "$APPS_DIR/$app_name"
    if ! docker build -f Dockerfile.bulletproof -t "$app_name:startup-test" . >/dev/null 2>&1; then
        print_error "Failed to build image for startup test"
        return 1
    fi
    
    # Start container
    if docker run -d --name "$app_name-startup-test" -p "$port:$port" "$app_name:startup-test" >/dev/null 2>&1; then
        print_status "Container started, waiting for startup..."
        
        # Wait for startup and test health endpoint
        local max_attempts=30
        local attempt=0
        
        while [[ $attempt -lt $max_attempts ]]; do
            if curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
                print_status "$app_name startup test PASSED! Health endpoint responding."
                
                # Cleanup
                docker stop "$app_name-startup-test" >/dev/null 2>&1
                docker rm "$app_name-startup-test" >/dev/null 2>&1
                docker rmi "$app_name:startup-test" >/dev/null 2>&1 || true
                
                return 0
            fi
            
            sleep 2
            ((attempt++))
        done
        
        print_error "$app_name startup test FAILED! Health endpoint not responding after 60 seconds."
        
        # Show logs for debugging
        print_status "Container logs for debugging:"
        docker logs "$app_name-startup-test" | tail -20
        
        # Cleanup
        docker stop "$app_name-startup-test" >/dev/null 2>&1
        docker rm "$app_name-startup-test" >/dev/null 2>&1
        docker rmi "$app_name:startup-test" >/dev/null 2>&1 || true
        
        return 1
    else
        print_error "Failed to start container for $app_name"
        docker rmi "$app_name:startup-test" >/dev/null 2>&1 || true
        return 1
    fi
}

# Main verification function
verify_app() {
    local app_name=$1
    local port=$2
    
    echo -e "${BLUE}=======================================${NC}"
    echo -e "${BLUE}Verifying $app_name Application${NC}"
    echo -e "${BLUE}=======================================${NC}"
    
    # Step 1: Verify file structure
    if ! verify_structure "$app_name"; then
        print_error "File structure verification failed for $app_name"
        return 1
    fi
    
    # Step 2: Verify dependencies
    if ! verify_dependencies "$app_name"; then
        print_error "Dependency verification failed for $app_name"
        return 1
    fi
    
    # Step 3: Test Docker build
    if ! test_build "$app_name"; then
        print_error "Docker build test failed for $app_name"
        return 1
    fi
    
    # Step 4: Test container startup
    if ! test_startup "$app_name" "$port"; then
        print_error "Container startup test failed for $app_name"
        return 1
    fi
    
    echo -e "${GREEN}✓ All verification tests passed for $app_name!${NC}"
    return 0
}

# Main execution
main() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}Zero-Downtime Pipeline: Build Verification${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    # Check prerequisites
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed or not in PATH"
        exit 1
    fi
    
    local overall_success=true
    
    # Verify Finance Trading App
    if ! verify_app "$FINANCE_APP" "8080"; then
        overall_success=false
    fi
    
    # Verify Pharma Manufacturing App  
    if ! verify_app "$PHARMA_APP" "8000"; then
        overall_success=false
    fi
    
    echo -e "${BLUE}================================================${NC}"
    if [[ "$overall_success" == "true" ]]; then
        echo -e "${GREEN}🎉 ALL VERIFICATION TESTS PASSED!${NC}"
        echo -e "${GREEN}Both applications are ready for deployment.${NC}"
        echo -e "${BLUE}Run ./build-and-deploy.sh to deploy to K3s.${NC}"
    else
        echo -e "${RED}❌ VERIFICATION TESTS FAILED!${NC}"
        echo -e "${RED}Please fix the issues above before deploying.${NC}"
        exit 1
    fi
    echo -e "${BLUE}================================================${NC}"
}

# Run main function
main "$@"