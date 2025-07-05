#!/bin/bash

set -euo pipefail

# Finance Trading System Deployment Script
# Implements zero-downtime deployment with trading hour awareness

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
NAMESPACE="finance-prod"
APP_NAME="finance-trading"
DEPLOYMENT_STRATEGY="${DEPLOYMENT_STRATEGY:-blue-green}"
ENVIRONMENT="${ENVIRONMENT:-production}"
KUBECTL_TIMEOUT="300s"
HEALTH_CHECK_TIMEOUT="120s"
SUCCESS_RATE_THRESHOLD="99.99"
LATENCY_THRESHOLD_MS="50"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if deployment is allowed during current time
check_trading_hours() {
    local current_hour=$(date -u +%H)
    local current_day=$(date -u +%u)  # 1=Monday, 7=Sunday
    local current_tz_hour=$(TZ=America/New_York date +%H)
    
    log "Checking trading hours... Current NY time: $(TZ=America/New_York date)"
    
    # Check if it's a weekday (Monday-Friday)
    if [ "$current_day" -ge 1 ] && [ "$current_day" -le 5 ]; then
        # Check if it's during NYSE/NASDAQ trading hours (9:30 AM - 4:00 PM EST)
        if [ "$current_tz_hour" -ge 9 ] && [ "$current_tz_hour" -lt 16 ]; then
            error "Deployment blocked: Currently during trading hours (9:30 AM - 4:00 PM EST)"
        fi
        
        # Check if it's during pre-market hours (4:00 AM - 9:30 AM EST)
        if [ "$current_tz_hour" -ge 4 ] && [ "$current_tz_hour" -lt 9 ]; then
            warn "Deployment during pre-market hours - proceed with caution"
        fi
    fi
    
    log "Trading hours check passed - deployment allowed"
}

# Validate market data feed connectivity
validate_market_data_feeds() {
    log "Validating market data feed connectivity..."
    
    # Get market data feed endpoints from ConfigMap
    local feeds=$(kubectl get configmap trading-config -n "$NAMESPACE" -o jsonpath='{.data.market-data-feeds}' | jq -r '.[] | .endpoint')
    
    for feed in $feeds; do
        log "Testing connectivity to $feed"
        if ! timeout 10 curl -s "$feed" > /dev/null; then
            error "Market data feed $feed is not accessible"
        fi
    done
    
    log "All market data feeds are accessible"
}

# Check current system health
check_system_health() {
    log "Checking current system health..."
    
    # Check if all pods are ready
    local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | tr ' ' '\n' | grep -c "True" || echo 0)
    local total_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" --no-headers | wc -l)
    
    if [ "$ready_pods" -ne "$total_pods" ]; then
        error "Not all pods are ready: $ready_pods/$total_pods"
    fi
    
    # Check success rate
    local success_rate=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8081/metrics | grep 'http_requests_total{.*code="200"' | awk '{print $2}' | head -1 || echo 0)
    log "Current success rate: $success_rate%"
    
    log "System health check passed"
}

# Perform blue-green deployment
blue_green_deploy() {
    log "Starting blue-green deployment..."
    
    # Determine current active color
    local current_color=$(kubectl get service "$APP_NAME"-service -n "$NAMESPACE" -o jsonpath='{.spec.selector.deployment-color}' || echo "blue")
    local new_color="green"
    
    if [ "$current_color" = "green" ]; then
        new_color="blue"
    fi
    
    log "Current active: $current_color, deploying to: $new_color"
    
    # Deploy to new color
    kubectl patch deployment "$APP_NAME"-app -n "$NAMESPACE" -p "{\"spec\":{\"selector\":{\"matchLabels\":{\"deployment-color\":\"$new_color\"}},\"template\":{\"metadata\":{\"labels\":{\"deployment-color\":\"$new_color\"}}}}}"
    
    # Wait for rollout
    kubectl rollout status deployment/"$APP_NAME"-app -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    
    # Health check new deployment
    perform_health_checks "$new_color"
    
    # Switch traffic
    kubectl patch service "$APP_NAME"-service -n "$NAMESPACE" -p "{\"spec\":{\"selector\":{\"deployment-color\":\"$new_color\"}}}"
    
    log "Blue-green deployment completed successfully"
}

# Perform canary deployment
canary_deploy() {
    log "Starting canary deployment..."
    
    # Deploy canary version
    kubectl apply -f "$PROJECT_ROOT/manifests/canary-deployment.yaml"
    
    # Wait for canary rollout
    kubectl rollout status deployment/"$APP_NAME"-canary -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    
    # Gradual traffic shift: 5% -> 25% -> 50% -> 100%
    local weights=(5 25 50 100)
    
    for weight in "${weights[@]}"; do
        log "Shifting $weight% traffic to canary..."
        
        # Update canary weight
        kubectl patch ingress "$APP_NAME"-canary-ingress -n "$NAMESPACE" -p "{\"metadata\":{\"annotations\":{\"nginx.ingress.kubernetes.io/canary-weight\":\"$weight\"}}}"
        
        # Monitor for 2 minutes
        sleep 120
        
        # Check canary health
        if ! perform_health_checks "canary"; then
            error "Canary health check failed, rolling back"
        fi
    done
    
    # Promote canary to main
    kubectl patch deployment "$APP_NAME"-app -n "$NAMESPACE" --type merge -p "{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"trading-engine\",\"image\":\"$(kubectl get deployment "$APP_NAME"-canary -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}')\"}]}}}}"
    
    # Clean up canary
    kubectl delete deployment "$APP_NAME"-canary -n "$NAMESPACE"
    kubectl delete ingress "$APP_NAME"-canary-ingress -n "$NAMESPACE"
    
    log "Canary deployment completed successfully"
}

# Perform comprehensive health checks
perform_health_checks() {
    local target_color="${1:-}"
    log "Performing health checks for $target_color deployment..."
    
    # Wait for pods to be ready
    local selector="app=$APP_NAME"
    if [ -n "$target_color" ]; then
        selector="$selector,deployment-color=$target_color"
    fi
    
    kubectl wait --for=condition=ready pod -l "$selector" -n "$NAMESPACE" --timeout="$HEALTH_CHECK_TIMEOUT"
    
    # Check latency
    log "Checking latency requirements..."
    local latency_check_count=0
    local max_latency_checks=10
    
    while [ $latency_check_count -lt $max_latency_checks ]; do
        local p99_latency=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8081/metrics | grep 'http_request_duration_seconds_bucket' | tail -1 | awk '{print $2}' || echo 0)
        local latency_ms=$(echo "$p99_latency * 1000" | bc -l)
        
        if (( $(echo "$latency_ms > $LATENCY_THRESHOLD_MS" | bc -l) )); then
            error "Latency check failed: ${latency_ms}ms > ${LATENCY_THRESHOLD_MS}ms"
        fi
        
        latency_check_count=$((latency_check_count + 1))
        sleep 5
    done
    
    # Check success rate
    log "Checking success rate requirements..."
    local success_rate_check_count=0
    local max_success_rate_checks=10
    
    while [ $success_rate_check_count -lt $max_success_rate_checks ]; do
        local success_rate=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8081/health/metrics | jq -r '.success_rate_percent' || echo 0)
        
        if (( $(echo "$success_rate < $SUCCESS_RATE_THRESHOLD" | bc -l) )); then
            error "Success rate check failed: ${success_rate}% < ${SUCCESS_RATE_THRESHOLD}%"
        fi
        
        success_rate_check_count=$((success_rate_check_count + 1))
        sleep 5
    done
    
    # Check market data connectivity
    log "Checking market data feed connectivity..."
    kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -f http://localhost:8083/feeds/status || error "Market data feed validation failed"
    
    log "All health checks passed"
    return 0
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."
    
    if [ "$DEPLOYMENT_STRATEGY" = "blue-green" ]; then
        # Switch back to previous color
        local current_color=$(kubectl get service "$APP_NAME"-service -n "$NAMESPACE" -o jsonpath='{.spec.selector.deployment-color}')
        local rollback_color="blue"
        
        if [ "$current_color" = "blue" ]; then
            rollback_color="green"
        fi
        
        kubectl patch service "$APP_NAME"-service -n "$NAMESPACE" -p "{\"spec\":{\"selector\":{\"deployment-color\":\"$rollback_color\"}}}"
    else
        # Standard rollback
        kubectl rollout undo deployment/"$APP_NAME"-app -n "$NAMESPACE"
        kubectl rollout status deployment/"$APP_NAME"-app -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    fi
    
    log "Rollback completed"
}

# Main deployment function
main() {
    log "Starting $APP_NAME deployment with $DEPLOYMENT_STRATEGY strategy"
    
    # Pre-deployment checks
    check_trading_hours
    validate_market_data_feeds
    check_system_health
    
    # Perform deployment based on strategy
    case "$DEPLOYMENT_STRATEGY" in
        "blue-green")
            blue_green_deploy
            ;;
        "canary")
            canary_deploy
            ;;
        *)
            error "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
            ;;
    esac
    
    # Final health check
    perform_health_checks
    
    log "Deployment completed successfully!"
}

# Trap to handle rollback on failure
trap 'error "Deployment failed, initiating rollback"; rollback_deployment' ERR

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strategy)
            DEPLOYMENT_STRATEGY="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --rollback)
            rollback_deployment
            exit 0
            ;;
        --force-trading-hours)
            log "WARNING: Forcing deployment during trading hours"
            check_trading_hours() { log "Trading hours check bypassed"; }
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --strategy STRATEGY    Deployment strategy (blue-green|canary)"
            echo "  --environment ENV      Environment (production|staging)"
            echo "  --rollback            Rollback to previous version"
            echo "  --force-trading-hours  Force deployment during trading hours"
            echo "  --help                Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main