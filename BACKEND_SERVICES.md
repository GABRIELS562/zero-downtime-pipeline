# Backend Services Deployment Guide

## Overview
This guide covers the deployment of two backend services:
- **Pharma Management System** (Port 30002)
- **Zero-Downtime Trading Platform** (Port 30003)

Both services are designed to work with the dashboard at `dashboard.jagdevops.co.za` (Port 30004).

## Architecture

```
┌─────────────────────────────────────────┐
│         Dashboard (Port 30004)          │
│      dashboard.jagdevops.co.za          │
└─────────────┬───────────────┬───────────┘
              │               │
     ┌────────▼──────┐  ┌────▼─────────┐
     │  Pharma App   │  │ Trading App  │
     │  Port 30002   │  │ Port 30003   │
     └───────────────┘  └──────────────┘
              │
     ┌────────▼──────────┐
     │   PostgreSQL      │
     │   (Optional)      │
     └───────────────────┘
```

## Services

### 1. Pharma Management System (Port 30002)
- **Purpose**: Pharmaceutical manufacturing monitoring
- **Features**:
  - FDA 21 CFR Part 11 compliance
  - Batch tracking
  - Equipment monitoring
  - Quality control
  - GMP compliance

**Endpoints**:
- `/` - Service information
- `/health/live` - Liveness probe
- `/api/v1/batches` - Batch management
- `/api/v1/equipment` - Equipment status
- `/api/v1/quality` - Quality control
- `/metrics` - Prometheus metrics

### 2. Trading Platform (Port 30003)
- **Purpose**: Financial trading platform
- **Features**:
  - Real-time market data
  - Order management
  - Portfolio tracking
  - < 10ms latency (demo)
  - SOX compliance

**Endpoints**:
- `/` - Service information
- `/health/live` - Liveness probe
- `/api/v1/market` - Market data
- `/api/v1/orders` - Order management
- `/api/v1/portfolio` - Portfolio view
- `/metrics` - Prometheus metrics

## Quick Start

### Prerequisites
- Docker installed and running
- Local Docker registry at `localhost:5000`
- Kubernetes cluster (optional for local testing)

### Local Testing
Test services locally with Docker:
```bash
./test-services-locally.sh
```

This will:
1. Build both services
2. Run them on ports 30002 and 30003
3. Display test results

### Build and Push to Registry
Build and push images to local registry:
```bash
./build-and-deploy-services.sh
```

### Deploy to Kubernetes
Deploy both services to Kubernetes:
```bash
./deploy-backend-services.sh
```

Or deploy individually:
```bash
# Deploy Pharma app
kubectl apply -f k8s-manifests/pharma-app-deployment.yaml
kubectl rollout restart deployment pharma-app -n production

# Deploy Trading app
kubectl apply -f k8s-manifests/finance-app-deployment.yaml
kubectl rollout restart deployment finance-app -n production
```

## File Structure

```
.
├── apps/
│   ├── pharma-manufacturing/
│   │   ├── app.py              # Flask application
│   │   ├── Dockerfile.flask    # Docker configuration
│   │   └── ...
│   └── finance-trading/
│       ├── app.py              # Flask application
│       ├── Dockerfile.flask    # Docker configuration
│       └── ...
├── k8s-manifests/
│   ├── pharma-app-deployment.yaml
│   ├── finance-app-deployment.yaml
│   └── postgresql-deployment.yaml
└── Scripts:
    ├── build-and-deploy-services.sh
    ├── deploy-backend-services.sh
    └── test-services-locally.sh
```

## Docker Images

Images are built and pushed to:
- `localhost:5000/pharma-app:production`
- `localhost:5000/finance-app:production`

## Kubernetes Configuration

Both services are deployed to the `production` namespace with:
- 2 replicas each
- Health checks configured
- NodePort services for external access
- Resource limits set

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n production
```

### View Logs
```bash
kubectl logs -f deployment/pharma-app -n production
kubectl logs -f deployment/finance-app -n production
```

### Test Health Endpoints
```bash
curl http://localhost:30002/health/live
curl http://localhost:30003/health/live
```

### Restart Services
```bash
kubectl rollout restart deployment pharma-app -n production
kubectl rollout restart deployment finance-app -n production
```

### Port Forwarding (if NodePort not available)
```bash
kubectl port-forward -n production svc/pharma-app 30002:8000
kubectl port-forward -n production svc/finance-app 30003:8000
```

## Integration with Dashboard

The dashboard at `dashboard.jagdevops.co.za` should be configured to connect to:
- Pharma API: `http://localhost:30002` or `http://pharma-app.production.svc.cluster.local:8000`
- Trading API: `http://localhost:30003` or `http://finance-app.production.svc.cluster.local:8000`

## Notes

- Both services are built as simple Flask applications for reliability
- They provide demo data and don't require external dependencies
- Health checks ensure Kubernetes can properly manage the services
- Services are stateless and can be scaled horizontally

## Support

For issues or questions:
1. Check pod logs for errors
2. Verify Docker registry is accessible
3. Ensure Kubernetes cluster is running
4. Test services locally first