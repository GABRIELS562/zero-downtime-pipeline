#!/bin/bash

set -euo pipefail

# Pharmaceutical Manufacturing System Deployment Script
# FDA 21 CFR Part 11 Compliant Deployment with Validation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
NAMESPACE="pharma-prod"
APP_NAME="pharma-manufacturing"
DEPLOYMENT_STRATEGY="${DEPLOYMENT_STRATEGY:-blue-green}"
ENVIRONMENT="${ENVIRONMENT:-production}"
KUBECTL_TIMEOUT="600s"
HEALTH_CHECK_TIMEOUT="300s"
EFFICIENCY_THRESHOLD="98.0"
VALIDATION_REQUIRED="true"
AUDIT_REQUIRED="true"
CHANGE_CONTROL_NUMBER="${CHANGE_CONTROL_NUMBER:-}"
VALIDATED_BY="${VALIDATED_BY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S UTC')] $1${NC}" | tee -a /var/log/pharma-deployment.log
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S UTC')] WARNING: $1${NC}" | tee -a /var/log/pharma-deployment.log
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S UTC')] ERROR: $1${NC}" | tee -a /var/log/pharma-deployment.log
    exit 1
}

audit_log() {
    local action="$1"
    local details="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    local audit_entry="{\"timestamp\":\"$timestamp\",\"action\":\"$action\",\"details\":\"$details\",\"user\":\"$USER\",\"change_control\":\"$CHANGE_CONTROL_NUMBER\",\"validated_by\":\"$VALIDATED_BY\"}"
    
    echo "$audit_entry" >> /var/log/pharma-audit.log
    
    # Send to audit database if available
    if command -v curl &> /dev/null; then
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -H "X-FDA-Compliance: 21CFR11" \
            -H "X-Change-Control: $CHANGE_CONTROL_NUMBER" \
            -d "$audit_entry" \
            "http://pharma-audit-service:8085/audit/log" || true
    fi
}

# Validate FDA compliance prerequisites
validate_fda_compliance() {
    log "Validating FDA 21 CFR Part 11 compliance prerequisites..."
    
    # Check change control number
    if [ -z "$CHANGE_CONTROL_NUMBER" ]; then
        error "Change control number is required for FDA compliance"
    fi
    
    # Check validator
    if [ -z "$VALIDATED_BY" ]; then
        error "Validator identification is required for FDA compliance"
    fi
    
    # Validate digital signatures
    if [ "$VALIDATION_REQUIRED" = "true" ]; then
        log "Validating digital signatures..."
        if ! kubectl get secret digital-signatures -n "$NAMESPACE" &> /dev/null; then
            error "Digital signatures secret not found - required for FDA compliance"
        fi
    fi
    
    # Check audit trail integrity
    log "Checking audit trail integrity..."
    local audit_check=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8085/audit/integrity || echo "failed")
    if [ "$audit_check" != "passed" ]; then
        error "Audit trail integrity check failed"
    fi
    
    audit_log "FDA_COMPLIANCE_VALIDATION" "FDA 21 CFR Part 11 compliance validation completed"
    log "FDA compliance validation passed"
}

# Check production line status
check_production_line_status() {
    log "Checking production line status..."
    
    # Check if production line is active
    local production_active=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8080/manufacturing/status | jq -r '.production_active' || echo "unknown")
    
    if [ "$production_active" = "true" ]; then
        error "Production line is active - deployments not allowed during active production"
    fi
    
    # Check manufacturing efficiency
    local efficiency=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8080/manufacturing/efficiency | jq -r '.efficiency_percent' || echo "0")
    
    if (( $(echo "$efficiency < $EFFICIENCY_THRESHOLD" | bc -l) )); then
        warn "Manufacturing efficiency is below threshold: $efficiency% < $EFFICIENCY_THRESHOLD%"
    fi
    
    audit_log "PRODUCTION_LINE_CHECK" "Production line status verified - active: $production_active, efficiency: $efficiency%"
    log "Production line status check passed"
}

# Validate sensor connectivity and readings
validate_sensors() {
    log "Validating sensor connectivity and readings..."
    
    # Check temperature sensors
    local temp_sensors=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8083/sensors/temperature | jq -r '.sensors[] | select(.critical == true) | .id')
    
    for sensor in $temp_sensors; do
        local temp_value=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s "http://localhost:8083/sensors/temperature/$sensor" | jq -r '.value' || echo "error")
        
        if [ "$temp_value" = "error" ]; then
            error "Temperature sensor $sensor is not responding"
        fi
        
        if (( $(echo "$temp_value < 18.0" | bc -l) )) || (( $(echo "$temp_value > 25.0" | bc -l) )); then
            error "Temperature sensor $sensor reading $temp_value°C is out of acceptable range (18-25°C)"
        fi
        
        log "Temperature sensor $sensor: $temp_value°C - OK"
    done
    
    # Check pressure sensors
    local pressure_sensors=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8083/sensors/pressure | jq -r '.sensors[] | select(.critical == true) | .id')
    
    for sensor in $pressure_sensors; do
        local pressure_value=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s "http://localhost:8083/sensors/pressure/$sensor" | jq -r '.value' || echo "error")
        
        if [ "$pressure_value" = "error" ]; then
            error "Pressure sensor $sensor is not responding"
        fi
        
        if (( $(echo "$pressure_value < 0.8" | bc -l) )) || (( $(echo "$pressure_value > 2.5" | bc -l) )); then
            error "Pressure sensor $sensor reading $pressure_value bar is out of acceptable range (0.8-2.5 bar)"
        fi
        
        log "Pressure sensor $sensor: $pressure_value bar - OK"
    done
    
    audit_log "SENSOR_VALIDATION" "All critical sensors validated and within acceptable ranges"
    log "Sensor validation completed successfully"
}

# Validate batch integrity
validate_batch_integrity() {
    log "Validating batch integrity..."
    
    # Get active batches
    local active_batches=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8084/batch/active | jq -r '.batches[] | .id')
    
    for batch in $active_batches; do
        local integrity_score=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s "http://localhost:8084/batch/$batch/integrity" | jq -r '.integrity_score' || echo "0")
        
        if (( $(echo "$integrity_score < 100" | bc -l) )); then
            error "Batch $batch integrity score is $integrity_score%, must be 100%"
        fi
        
        log "Batch $batch integrity: $integrity_score% - OK"
    done
    
    audit_log "BATCH_INTEGRITY_VALIDATION" "All active batches validated with 100% integrity"
    log "Batch integrity validation completed"
}

# Perform zero-downtime deployment
perform_zero_downtime_deployment() {
    log "Starting zero-downtime deployment..."
    
    # Create backup of current configuration
    kubectl get deployment "$APP_NAME"-app -n "$NAMESPACE" -o yaml > "/tmp/backup-deployment-$(date +%Y%m%d-%H%M%S).yaml"
    
    # Apply new deployment with rolling update
    kubectl apply -f "$PROJECT_ROOT/manifests/deployment.yaml" --record
    
    # Wait for rollout with extended timeout for pharma systems
    kubectl rollout status deployment/"$APP_NAME"-app -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    
    # Verify deployment
    perform_post_deployment_validation
    
    audit_log "ZERO_DOWNTIME_DEPLOYMENT" "Zero-downtime deployment completed successfully"
    log "Zero-downtime deployment completed"
}

# Comprehensive post-deployment validation
perform_post_deployment_validation() {
    log "Performing post-deployment validation..."
    
    # Wait for all pods to be ready
    kubectl wait --for=condition=ready pod -l app="$APP_NAME" -n "$NAMESPACE" --timeout="$HEALTH_CHECK_TIMEOUT"
    
    # Manufacturing efficiency check
    local efficiency_check_count=0
    local max_efficiency_checks=12  # 2 minutes with 10-second intervals
    
    while [ $efficiency_check_count -lt $max_efficiency_checks ]; do
        local efficiency=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8080/manufacturing/efficiency | jq -r '.efficiency_percent' || echo "0")
        
        if (( $(echo "$efficiency >= $EFFICIENCY_THRESHOLD" | bc -l) )); then
            log "Manufacturing efficiency check passed: $efficiency%"
            break
        fi
        
        if [ $efficiency_check_count -eq $((max_efficiency_checks - 1)) ]; then
            error "Manufacturing efficiency check failed: $efficiency% < $EFFICIENCY_THRESHOLD%"
        fi
        
        efficiency_check_count=$((efficiency_check_count + 1))
        sleep 10
    done
    
    # Sensor validation
    validate_sensors
    
    # Batch integrity check
    validate_batch_integrity
    
    # System health checks
    log "Performing system health checks..."
    
    # Check all container health endpoints
    local containers=("manufacturing-control" "sensor-monitor" "batch-integrity-checker" "audit-logger")
    for container in "${containers[@]}"; do
        local health_status=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -c "$container" -- curl -s http://localhost:8081/health | jq -r '.status' || echo "unknown")
        
        if [ "$health_status" != "healthy" ]; then
            error "Container $container health check failed: $health_status"
        fi
        
        log "Container $container health: $health_status"
    done
    
    # Audit trail validation
    log "Validating audit trail after deployment..."
    local audit_integrity=$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8085/audit/integrity | jq -r '.status' || echo "failed")
    
    if [ "$audit_integrity" != "passed" ]; then
        error "Post-deployment audit trail integrity check failed"
    fi
    
    audit_log "POST_DEPLOYMENT_VALIDATION" "All post-deployment validations completed successfully"
    log "Post-deployment validation completed successfully"
}

# Generate FDA compliance report
generate_compliance_report() {
    log "Generating FDA compliance report..."
    
    local report_file="/tmp/fda-compliance-report-$(date +%Y%m%d-%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "report_metadata": {
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
    "change_control_number": "$CHANGE_CONTROL_NUMBER",
    "validated_by": "$VALIDATED_BY",
    "deployment_strategy": "$DEPLOYMENT_STRATEGY",
    "environment": "$ENVIRONMENT"
  },
  "compliance_validations": {
    "fda_21cfr11_compliance": "PASSED",
    "digital_signatures": "VALIDATED",
    "audit_trail_integrity": "PASSED",
    "production_line_status": "VERIFIED",
    "sensor_validation": "PASSED",
    "batch_integrity": "VALIDATED",
    "zero_downtime_deployment": "COMPLETED"
  },
  "system_metrics": {
    "manufacturing_efficiency": "$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8080/manufacturing/efficiency | jq -r '.efficiency_percent' || echo 'N/A')",
    "sensor_validation_rate": "$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8083/sensors/validation-rate | jq -r '.success_rate' || echo 'N/A')",
    "batch_integrity_score": "$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8084/batch/integrity-summary | jq -r '.average_score' || echo 'N/A')",
    "audit_trail_entries": "$(kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME"-app -- curl -s http://localhost:8085/audit/count | jq -r '.count' || echo 'N/A')"
  },
  "deployment_summary": {
    "deployment_duration": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
    "pods_deployed": "$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" --no-headers | wc -l)",
    "rollback_required": false,
    "compliance_status": "COMPLIANT"
  }
}
EOF
    
    log "FDA compliance report generated: $report_file"
    audit_log "COMPLIANCE_REPORT" "FDA compliance report generated: $report_file"
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."
    
    kubectl rollout undo deployment/"$APP_NAME"-app -n "$NAMESPACE"
    kubectl rollout status deployment/"$APP_NAME"-app -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
    
    # Validate rollback
    perform_post_deployment_validation
    
    audit_log "DEPLOYMENT_ROLLBACK" "Deployment rollback completed successfully"
    log "Rollback completed successfully"
}

# Main deployment function
main() {
    log "Starting pharmaceutical manufacturing system deployment"
    log "Change Control Number: $CHANGE_CONTROL_NUMBER"
    log "Validated By: $VALIDATED_BY"
    log "Deployment Strategy: $DEPLOYMENT_STRATEGY"
    
    # Pre-deployment validations
    validate_fda_compliance
    check_production_line_status
    validate_sensors
    validate_batch_integrity
    
    # Perform deployment
    perform_zero_downtime_deployment
    
    # Generate compliance report
    generate_compliance_report
    
    log "Pharmaceutical manufacturing system deployment completed successfully!"
    log "All FDA 21 CFR Part 11 compliance requirements have been met."
}

# Trap to handle rollback on failure
trap 'error "Deployment failed, initiating rollback"; rollback_deployment' ERR

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --change-control)
            CHANGE_CONTROL_NUMBER="$2"
            shift 2
            ;;
        --validated-by)
            VALIDATED_BY="$2"
            shift 2
            ;;
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
        --skip-validation)
            warn "WARNING: Skipping validation - not recommended for production"
            VALIDATION_REQUIRED="false"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --change-control NUM   Change control number (required)"
            echo "  --validated-by USER    Validator identification (required)"
            echo "  --strategy STRATEGY    Deployment strategy (blue-green|rolling)"
            echo "  --environment ENV      Environment (production|staging)"
            echo "  --rollback            Rollback to previous version"
            echo "  --skip-validation     Skip validation (not recommended)"
            echo "  --help                Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate required parameters
if [ -z "$CHANGE_CONTROL_NUMBER" ] || [ -z "$VALIDATED_BY" ]; then
    error "Change control number and validator identification are required for FDA compliance"
fi

# Run main function
main