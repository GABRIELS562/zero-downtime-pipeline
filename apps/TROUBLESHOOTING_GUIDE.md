# Zero-Downtime Pipeline: Bulletproof Deployment Guide

## ROOT CAUSE ANALYSIS & SOLUTIONS

### Issues Identified and Fixed

#### 1. **Missing Dependencies in requirements-working.txt**
**Problem:** The `requirements-working.txt` file was missing critical dependencies like `alpha-vantage`, `pandas`, `numpy`, etc.

**Solution:** Created `requirements-bulletproof.txt` files with all necessary dependencies:
- `/Users/user/zero-downtime-pipeline/apps/finance-trading/requirements-bulletproof.txt`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/requirements-bulletproof.txt`

#### 2. **Missing __init__.py Files in Pharma App**
**Problem:** The pharma app was missing ALL `__init__.py` files, causing Python import failures.

**Solution:** Created all necessary `__init__.py` files:
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/__init__.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/api/__init__.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/services/__init__.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/middleware/__init__.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/models/__init__.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/database/__init__.py`

#### 3. **Missing Service Files in Pharma App**
**Problem:** The pharma app's main.py tried to import services that didn't exist.

**Solution:** Created missing service files:
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/services/database_manager.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/services/alert_manager.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/services/equipment_simulator.py`

#### 4. **Inconsistent Import Paths**
**Problem:** Finance app mixed `from src.` and direct imports without `src.`

**Solution:** Fixed all imports in main.py to use consistent `from src.` prefix.

#### 5. **Container Build Process Issues**
**Problem:** Using incomplete requirements file and suboptimal Dockerfile structure.

**Solution:** Created bulletproof Dockerfiles:
- `/Users/user/zero-downtime-pipeline/apps/finance-trading/Dockerfile.bulletproof`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/Dockerfile.bulletproof`

## STEP-BY-STEP BUILD AND DEPLOYMENT

### Prerequisites
```bash
# Verify Docker is running
docker --version

# Verify kubectl can connect to K3s
kubectl cluster-info

# Verify curl is available for health checks
curl --version
```

### Step 1: Verify Build Environment
```bash
cd /Users/user/zero-downtime-pipeline/apps
./verify-build.sh
```

This script will:
- Check file structure completeness
- Verify all Python dependencies can be installed
- Test Docker builds
- Test container startup and health endpoints

### Step 2: Build and Deploy (if verification passes)
```bash
cd /Users/user/zero-downtime-pipeline/apps
./build-and-deploy.sh
```

This script will:
- Build both Docker images using bulletproof Dockerfiles
- Test images locally
- Deploy to K3s with zero-downtime rolling updates
- Verify deployments are healthy

### Step 3: Manual Build (if needed)

#### Finance Trading App
```bash
cd /Users/user/zero-downtime-pipeline/apps/finance-trading

# Build image
docker build -f Dockerfile.bulletproof -t finance-trading:latest .

# Test locally
docker run -d --name finance-test -p 8080:8080 finance-trading:latest

# Check health
curl http://localhost:8080/health

# Stop test
docker stop finance-test && docker rm finance-test
```

#### Pharma Manufacturing App
```bash
cd /Users/user/zero-downtime-pipeline/apps/pharma-manufacturing

# Build image
docker build -f Dockerfile.bulletproof -t pharma-manufacturing:latest .

# Test locally
docker run -d --name pharma-test -p 8000:8000 pharma-manufacturing:latest

# Check health
curl http://localhost:8000/health

# Stop test
docker stop pharma-test && docker rm pharma-test
```

### Step 4: Manual K3s Deployment

#### Load Images into K3s
```bash
docker save finance-trading:latest | sudo k3s ctr images import -
docker save pharma-manufacturing:latest | sudo k3s ctr images import -
```

#### Deploy Finance Trading
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finance-trading
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: finance-trading
  template:
    metadata:
      labels:
        app: finance-trading
    spec:
      containers:
      - name: finance-trading
        image: finance-trading:latest
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: finance-trading-service
spec:
  selector:
    app: finance-trading
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
EOF
```

#### Deploy Pharma Manufacturing
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pharma-manufacturing
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: pharma-manufacturing
  template:
    metadata:
      labels:
        app: pharma-manufacturing
    spec:
      containers:
      - name: pharma-manufacturing
        image: pharma-manufacturing:latest
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: pharma-manufacturing-service
spec:
  selector:
    app: pharma-manufacturing
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
EOF
```

## VERIFICATION STEPS

### Check Deployment Status
```bash
# Check deployments
kubectl get deployments

# Check pods
kubectl get pods

# Check services
kubectl get services

# Check specific app logs
kubectl logs -l app=finance-trading --tail=20
kubectl logs -l app=pharma-manufacturing --tail=20
```

### Test Applications
```bash
# Port forward to test locally
kubectl port-forward service/finance-trading-service 8080:8080 &
kubectl port-forward service/pharma-manufacturing-service 8000:8000 &

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8000/health

curl http://localhost:8080/
curl http://localhost:8000/

# Stop port forwarding
kill %1 %2
```

## TROUBLESHOOTING COMMON ISSUES

### Issue: "ModuleNotFoundError: No module named 'httpx'"
**Solution:** Ensure using `requirements-bulletproof.txt` which includes all dependencies.

### Issue: "ModuleNotFoundError: No module named 'src.services.batch_service'"
**Solution:** Check that all `__init__.py` files exist and PYTHONPATH is set correctly.

### Issue: Container fails to start
**Debug Steps:**
```bash
# Check container logs
docker logs <container-name>

# Run container interactively
docker run -it --entrypoint /bin/bash <image-name>

# Check if Python can find modules
docker run -it <image-name> python -c "import sys; print(sys.path)"
```

### Issue: Health checks fail
**Debug Steps:**
```bash
# Check if app is listening on correct port
docker run <image-name> netstat -tlnp

# Test health endpoint manually
docker exec -it <container-name> curl http://localhost:<port>/health
```

### Issue: K3s deployment fails
**Debug Steps:**
```bash
# Describe deployment
kubectl describe deployment <app-name>

# Check pod events
kubectl describe pod <pod-name>

# Check resource usage
kubectl top pods
kubectl top nodes
```

## KEY FILES CREATED/MODIFIED

### Bulletproof Requirements
- `/Users/user/zero-downtime-pipeline/apps/finance-trading/requirements-bulletproof.txt`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/requirements-bulletproof.txt`

### Bulletproof Dockerfiles
- `/Users/user/zero-downtime-pipeline/apps/finance-trading/Dockerfile.bulletproof`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/Dockerfile.bulletproof`

### Missing Service Files (Pharma)
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/services/database_manager.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/services/alert_manager.py`
- `/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src/services/equipment_simulator.py`

### Deployment Scripts
- `/Users/user/zero-downtime-pipeline/apps/build-and-deploy.sh`
- `/Users/user/zero-downtime-pipeline/apps/verify-build.sh`

### __init__.py Files (Pharma)
- All necessary `__init__.py` files in pharma app src structure

## SUCCESS CRITERIA

✅ Both applications build successfully without errors
✅ All Python dependencies install correctly
✅ All imports resolve without ModuleNotFoundError
✅ Containers start and respond to health checks
✅ Applications deploy to K3s with zero downtime
✅ Health checks pass in Kubernetes
✅ Services are accessible through Kubernetes services

The bulletproof configuration addresses all the root causes and provides a reliable deployment pipeline for both applications.