# PROJECT STRUCTURE - ZERO-DOWNTIME PIPELINE
## With Forensic Evidence Collector (Clean Deployment Ready)

```
zero-downtime-pipeline/
│
├── DEPLOYMENT_GUIDE.md             # Main deployment guide (START HERE!)
├── QUICK_REFERENCE.md             # Essential commands reference
├── PROJECT_STRUCTURE.md           # This file
├── README.md                       # Project overview
│
├── forensic-collector/             # YOUR DIFFERENTIATOR
│   ├── docker/
│   │   └── Dockerfile.forensic    # Forensic collector image
│   ├── kubernetes/
│   │   └── forensic-collector-daemonset.yaml  # K3s deployment
│   └── scripts/
│       ├── forensic_collector.py  # Core collector logic
│       └── forensic_api.py        # Web interface
│
├── apps/
│   ├── finance-trading/           # SOX-compliant trading app (Server 1)
│   │   ├── docker-compose.yml     # Docker deployment
│   │   ├── src/                   # Application source
│   │   ├── scripts/               # Deployment scripts
│   │   └── manifests/             # K8s manifests (optional)
│   │
│   └── pharma-manufacturing/      # GMP-compliant pharma app (Server 2)
│       ├── docker-compose.yml     # Docker deployment
│       ├── src/                   # Application source
│       ├── scripts/               # Deployment scripts
│       └── manifests/             # K8s manifests (optional)
│
├── scripts/                        # Infrastructure scripts
│   ├── backup-k3s.sh              # K3s cluster backup
│   ├── backup-forensics.sh        # Evidence backup
│   └── disaster-recovery-test.sh  # DR test (run 3x!)
│
├── monitoring/                     # Monitoring configurations
│   └── grafana/
│       └── provisioning/          # Dashboard configs
│
├── dashboards/                     # Grafana dashboard JSONs
│   ├── deployment-performance-mttr.json
│   ├── executive-deployment-overview.json
│   ├── finance-trading-business-impact.json
│   └── pharma-manufacturing-efficiency.json
│
├── infrastructure/                 # Infrastructure configurations
│   ├── monitoring/
│   ├── health-checks/
│   └── rollback-automation/
│
├── argocd/                        # GitOps configurations
│   ├── applications/
│   └── projects/
│
├── health-checks/                 # Health check scripts
│   ├── common/
│   ├── finance/
│   ├── pharma/
│   └── infrastructure/
│
├── frontend/                      # Demo dashboards
│   └── index.html                 # Status page
│
└── archive/                       # Archived files (DO NOT USE)
    ├── old_docs/                  # Old documentation
    ├── old_scripts/               # Old scripts
    ├── old_deployments/           # Old deployment files
    ├── terraform/                 # Terraform (not needed)
    ├── canary/                    # Canary deployments
    ├── rollback/                  # Rollback automation
    ├── sre/                       # SRE docs
    └── tests/                     # Test files
```

## DEPLOYMENT ARCHITECTURE

### Server 1 (16GB RAM) - Production Apps
- **K3s Cluster**: Lightweight Kubernetes
- **LIMS Application**: FDA 21 CFR Part 11 compliant (K3s)
- **Jenkins CI/CD**: FDA approval gates (K3s)
- **Finance Trading App**: SOX compliant (Docker standalone)
- **Forensic Collector DaemonSet**: Monitors K3s pods

### Server 2 (16GB RAM) - DevOps & Monitoring
- **Pharma Manufacturing App**: GMP compliant (Docker)
- **ArgoCD**: GitOps for Pharma app
- **Prometheus + Grafana**: Master monitoring
- **Loki**: Log aggregation (NOT Elasticsearch)
- **Forensic Agent Container**: Monitors Docker containers
- **Forensic Chain Database**: Central evidence storage

### EC2 t2.micro (1GB RAM) - Gateway
- **Nginx**: Reverse proxy
- **Tailscale**: Secure mesh networking
- **Status Page**: Public demo access
- **Evidence Backup**: Critical incidents only

## KEY FILES FOR DEPLOYMENT

### Essential Files Only
```
✅ DEPLOYMENT_GUIDE.md              # Follow this step-by-step
✅ QUICK_REFERENCE.md               # Command reference
✅ forensic-collector/*             # Build and deploy on Day 4
✅ apps/finance-trading/*           # Deploy on Server 1
✅ apps/pharma-manufacturing/*      # Deploy on Server 2
✅ scripts/backup-*.sh              # Backup scripts
✅ scripts/disaster-recovery-test.sh # Run 3x on Day 6
✅ monitoring/grafana/*             # Monitoring setup
✅ dashboards/*.json                # Import to Grafana
```

### DO NOT USE (Archived)
```
❌ archive/*                        # Old files, not needed
❌ terraform/*                      # Cloud deployment (not for home lab)
❌ tests/*                          # Unit tests
❌ Old deployment guides            # Use DEPLOYMENT_GUIDE.md instead
```

## DEPLOYMENT CONFIRMATION

### YES, You Can Deploy Apps on Different Servers:

**Server 1 Deployment:**
- LIMS in K3s namespace
- Jenkins in K3s namespace  
- Finance Trading as Docker containers
- Forensic Collector as K3s DaemonSet

**Server 2 Deployment:**
- Pharma Manufacturing as Docker containers
- ArgoCD in K3s (optional) or Docker
- Prometheus/Grafana as Docker containers
- Loki as Docker container
- Forensic Agent as Docker container

This separation provides:
- Better resource utilization
- Clear separation of concerns
- Easier troubleshooting
- Realistic production architecture

## QUICK START COMMANDS

```bash
# Day 1 - Server 1
curl -sfL https://get.k3s.io | sh -
docker-compose -f apps/finance-trading/docker-compose.yml up -d

# Day 1 - Server 2  
curl -fsSL https://get.docker.com | sh
docker-compose -f apps/pharma-manufacturing/docker-compose.yml up -d

# Day 4 - Forensic Collector (Critical!)
docker build -t forensic-collector:latest -f forensic-collector/docker/Dockerfile.forensic .
kubectl apply -f forensic-collector/kubernetes/forensic-collector-daemonset.yaml

# Day 6 - Disaster Recovery Test
./scripts/disaster-recovery-test.sh  # Run 3 times!
```

## SUCCESS CRITERIA

- [ ] Finance app running on Server 1 (Docker)
- [ ] Pharma app running on Server 2 (Docker)
- [ ] LIMS running on Server 1 (K3s)
- [ ] Forensic collector capturing incidents
- [ ] Evidence chain verified
- [ ] DR test passed 3 times
- [ ] Cost under $25/month
- [ ] Demo practiced 10+ times

## YOUR UNIQUE VALUE PROPOSITION

**"I built a forensic evidence collector for DevOps infrastructure, applying crime scene investigation principles to system monitoring. This isn't from a tutorial - it's an innovation from my forensic science background."**

---

**START HERE:** Open DEPLOYMENT_GUIDE.md and begin with Day 1!