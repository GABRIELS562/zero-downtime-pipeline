# Zero-Downtime Deployment Pipeline

## Overview

Production-grade GitOps implementation demonstrating zero-downtime deployments for Finance Trading and Pharma Management applications using ArgoCD on Kubernetes (K3s).

## 🚀 Live Applications

- **DevOps Dashboard**: https://dashboard.jagdevops.co.za
- **Finance Trading**: https://finance.jagdevops.co.za  
- **Pharma Management**: https://pharma.jagdevops.co.za

## 📸 Production Screenshots

### DevOps Dashboard
![Dashboard](docs/screenshots/dashboard.png)
*Zero-Downtime Trading System interface*

### ArgoCD GitOps
![ArgoCD](docs/screenshots/argocd.png)
*Automated deployment management*

### Applications Running
![Apps](docs/screenshots/apps.png)
*Finance and Pharma with 2 replicas each*

## 🏗️ Architecture

```
Production Infrastructure:
├── K3s Cluster (192.168.50.100)
│   ├── Finance App (2 replicas - zero downtime)
│   ├── Pharma Frontend (2 replicas - zero downtime)
│   └── Dashboard (monitoring interface)
├── ArgoCD (GitOps automation)
├── Jenkins (Build pipeline)
└── Docker Registry (localhost:5000)

Monitoring Stack (192.168.50.74):
├── Grafana (Metrics visualization)
├── Loki (Log aggregation)
└── Prometheus (Metrics collection)
```

## 📊 Zero-Downtime Strategy

### Rolling Update Configuration
```yaml
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
```

Ensures continuous availability during deployments.

## 🔄 GitOps Workflow

1. **Code Push** → GitHub repository
2. **Jenkins Build** → Docker image creation
3. **Manifest Update** → K8s YAML files updated
4. **ArgoCD Sync** → Automated deployment (3-min interval)
5. **Rolling Update** → Zero-downtime deployment
6. **Health Checks** → Validate new pods before traffic shift

## 📁 Repository Structure

```
zero-downtime-pipeline/
├── k8s/
│   ├── finance-deployment.yaml
│   └── pharma-deployment.yaml
├── frontend/
│   ├── index.html              # Dashboard
│   └── pharma-dashboard.html   # Pharma UI
├── argocd/
│   └── application.yaml
├── monitoring/
├── Jenkinsfile
└── README.md
```

## 🚀 Deployment Management

### ArgoCD Application
```bash
Application: zero-downtime-app
Repository: https://github.com/GABRIELS562/zero-downtime-pipeline
Path: k8s/
Sync: Automated (self-heal enabled)
```

### Verify Deployments
```bash
# Check application status
kubectl get deployments -n production

# Monitor rolling updates
kubectl rollout status deployment/finance-app -n production
kubectl rollout status deployment/pharma-frontend -n production

# View ArgoCD sync
kubectl get applications -n argocd
```

## 📈 Monitoring

- **Grafana**: http://192.168.50.74:3000
- **ArgoCD UI**: http://192.168.50.100:30443

## 🛠️ Technologies

- **Kubernetes**: K3s lightweight distribution
- **GitOps**: ArgoCD for declarative deployments
- **CI/CD**: Jenkins for build automation
- **Monitoring**: Prometheus, Grafana, Loki stack
- **Ingress**: Cloudflare tunnels for HTTPS
- **Registry**: Docker Registry v2

## 📊 Production Metrics

- **Deployment Frequency**: Multiple daily deployments
- **Rollback Time**: <1 minute via ArgoCD
- **Recovery Time**: <60 seconds (demonstrated)
- **Availability**: Zero downtime during updates
- **Replicas**: 2 per application for HA

## 🚨 Resilience Demonstrated

Successfully recovered from production incident:
- Accidental resource deletion
- Recovery in <60 seconds
- No data loss
- Improved configuration (disabled aggressive pruning)

## 🔗 Related Projects

- [LIMS Application](https://github.com/GABRIELS562/JAG-LABSCIENTIFIC-DNA) - Jenkins CI/CD
- [Portfolio Overview](https://github.com/GABRIELS562)

## 📝 License

MIT

---
*JAG DevOps Portfolio - Production-grade zero-downtime deployments with GitOps, demonstrating enterprise-level DevOps practices*
