#!/bin/bash

###############################################################################
# T2.MICRO DEPLOYMENT SCRIPT
# Optimized deployment for AWS t2.micro instance (1GB RAM, 1 vCPU)
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_MODE=${1:-frontend}  # Options: frontend, finance, pharma, monitoring, full
MAX_WAIT_TIME=120  # Maximum time to wait for services (seconds)

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Zero-Downtime Pipeline - T2.MICRO Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Function to check system resources
check_resources() {
    echo -e "\n${YELLOW}📊 Checking System Resources...${NC}"
    
    # Check memory
    TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
    AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
    MEM_PERCENT=$((100 - (AVAILABLE_MEM * 100 / TOTAL_MEM)))
    
    echo "  Memory: ${AVAILABLE_MEM}MB available of ${TOTAL_MEM}MB (${MEM_PERCENT}% used)"
    
    # Check disk space
    DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
    DISK_AVAILABLE=$(df -h / | awk 'NR==2{print $4}')
    
    echo "  Disk: ${DISK_AVAILABLE} available (${DISK_USAGE}% used)"
    
    # Check CPU
    CPU_COUNT=$(nproc)
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')
    
    echo "  CPU: ${CPU_COUNT} core(s), Load:${LOAD_AVG}"
    
    # Warning if resources are low
    if [ $MEM_PERCENT -gt 80 ]; then
        echo -e "${RED}  ⚠️  WARNING: Memory usage is high (${MEM_PERCENT}%)${NC}"
        echo "  Consider stopping unnecessary services"
    fi
    
    if [ $DISK_USAGE -gt 80 ]; then
        echo -e "${RED}  ⚠️  WARNING: Disk usage is high (${DISK_USAGE}%)${NC}"
        echo "  Consider cleaning up Docker images: docker system prune -a"
    fi
}

# Function to stop all services
stop_all_services() {
    echo -e "\n${YELLOW}🛑 Stopping existing services...${NC}"
    docker-compose -f docker-compose.t2micro.yml down 2>/dev/null || true
    docker system prune -f --volumes 2>/dev/null || true
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Function to deploy frontend only
deploy_frontend() {
    echo -e "\n${BLUE}🌐 Deploying Frontend (Nginx)...${NC}"
    docker-compose -f docker-compose.t2micro.yml up -d frontend
    
    echo -e "${YELLOW}⏳ Waiting for frontend to be healthy...${NC}"
    sleep 5
    
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is running at http://$(curl -s ifconfig.me)${NC}"
    else
        echo -e "${RED}❌ Frontend health check failed${NC}"
        return 1
    fi
}

# Function to deploy finance app
deploy_finance() {
    echo -e "\n${BLUE}💹 Deploying Finance Trading App...${NC}"
    
    # Build the image first
    echo "Building Finance Trading image..."
    docker-compose -f docker-compose.t2micro.yml build finance-trading
    
    # Start the service
    docker-compose -f docker-compose.t2micro.yml --profile finance up -d
    
    echo -e "${YELLOW}⏳ Waiting for Finance app to be healthy...${NC}"
    
    # Wait for health check
    COUNTER=0
    while [ $COUNTER -lt $MAX_WAIT_TIME ]; do
        if curl -f http://localhost:8080/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Finance Trading app is running at http://$(curl -s ifconfig.me):8080${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        COUNTER=$((COUNTER + 2))
    done
    
    echo -e "${RED}❌ Finance app failed to start within ${MAX_WAIT_TIME} seconds${NC}"
    docker-compose -f docker-compose.t2micro.yml logs finance-trading
    return 1
}

# Function to deploy pharma app
deploy_pharma() {
    echo -e "\n${BLUE}💊 Deploying Pharma Manufacturing App...${NC}"
    
    # Build the image first
    echo "Building Pharma Manufacturing image..."
    docker-compose -f docker-compose.t2micro.yml build pharma-manufacturing
    
    # Start the service
    docker-compose -f docker-compose.t2micro.yml --profile pharma up -d
    
    echo -e "${YELLOW}⏳ Waiting for Pharma app to be healthy...${NC}"
    
    # Wait for health check
    COUNTER=0
    while [ $COUNTER -lt $MAX_WAIT_TIME ]; do
        if curl -f http://localhost:8090/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Pharma Manufacturing app is running at http://$(curl -s ifconfig.me):8090${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        COUNTER=$((COUNTER + 2))
    done
    
    echo -e "${RED}❌ Pharma app failed to start within ${MAX_WAIT_TIME} seconds${NC}"
    docker-compose -f docker-compose.t2micro.yml logs pharma-manufacturing
    return 1
}

# Function to deploy monitoring
deploy_monitoring() {
    echo -e "\n${BLUE}📊 Deploying Monitoring Stack...${NC}"
    docker-compose -f docker-compose.t2micro.yml --profile monitoring up -d
    
    echo -e "${YELLOW}⏳ Waiting for Prometheus...${NC}"
    sleep 10
    
    if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Prometheus is running at http://$(curl -s ifconfig.me):9090${NC}"
    else
        echo -e "${YELLOW}⚠️  Prometheus may still be starting up${NC}"
    fi
}

# Function to show running services
show_status() {
    echo -e "\n${BLUE}📋 Service Status:${NC}"
    docker-compose -f docker-compose.t2micro.yml ps
    
    echo -e "\n${BLUE}📊 Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Function to show logs
show_logs() {
    echo -e "\n${BLUE}📜 Recent Logs:${NC}"
    docker-compose -f docker-compose.t2micro.yml logs --tail=20
}

# Main deployment logic
main() {
    echo -e "${YELLOW}🚀 Starting deployment: ${DEPLOY_MODE}${NC}"
    
    # Check prerequisites
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Check system resources
    check_resources
    
    # Execute deployment based on mode
    case $DEPLOY_MODE in
        frontend)
            stop_all_services
            deploy_frontend
            ;;
        finance)
            stop_all_services
            deploy_frontend
            deploy_finance
            ;;
        pharma)
            stop_all_services
            deploy_frontend
            deploy_pharma
            ;;
        monitoring)
            deploy_monitoring
            ;;
        full)
            echo -e "${RED}⚠️  WARNING: Full deployment not recommended for t2.micro${NC}"
            echo "Deploying services sequentially..."
            stop_all_services
            deploy_frontend
            deploy_finance
            sleep 5
            deploy_pharma
            deploy_monitoring
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        stop)
            stop_all_services
            ;;
        *)
            echo -e "${RED}Invalid mode: $DEPLOY_MODE${NC}"
            echo "Usage: $0 [frontend|finance|pharma|monitoring|full|status|logs|stop]"
            exit 1
            ;;
    esac
    
    # Show final status
    if [ "$DEPLOY_MODE" != "status" ] && [ "$DEPLOY_MODE" != "logs" ] && [ "$DEPLOY_MODE" != "stop" ]; then
        show_status
        
        echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}     Deployment Complete!${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        
        echo -e "\n${BLUE}📌 Access Points:${NC}"
        PUBLIC_IP=$(curl -s ifconfig.me)
        echo "  Frontend: http://${PUBLIC_IP}"
        
        if docker ps | grep -q finance-app; then
            echo "  Finance API: http://${PUBLIC_IP}:8080"
        fi
        
        if docker ps | grep -q pharma-app; then
            echo "  Pharma API: http://${PUBLIC_IP}:8090"
        fi
        
        if docker ps | grep -q prometheus; then
            echo "  Prometheus: http://${PUBLIC_IP}:9090"
        fi
        
        echo -e "\n${YELLOW}💡 Tips:${NC}"
        echo "  • Monitor resources: docker stats"
        echo "  • View logs: ./deploy-t2micro.sh logs"
        echo "  • Check status: ./deploy-t2micro.sh status"
        echo "  • Stop all: ./deploy-t2micro.sh stop"
    fi
}

# Run main function
main