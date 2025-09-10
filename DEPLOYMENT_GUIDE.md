# DEPLOYMENT GUIDE - 6-DAY IMPLEMENTATION
## Zero-Downtime Pipeline with Forensic Evidence Collector

---

## PRE-DEPLOYMENT CHECKLIST

### Infrastructure Requirements
- [ ] **Server 1:** 16GB RAM Ubuntu 22.04 LTS (K3s + LIMS + Finance Trading)
- [ ] **Server 2:** 16GB RAM Ubuntu 22.04 LTS (Pharma + Monitoring + DevOps Tools)  
- [ ] **EC2:** t2.micro instance (Gateway)
- [ ] **Network:** Tailscale account created
- [ ] **Backup:** UPS battery backup connected
- [ ] **Internet:** Cellular failover configured

### Software Prerequisites
```bash
# Install on both servers
sudo apt update && sudo apt install -y \
    curl wget git docker.io docker-compose \
    python3 python3-pip sqlite3 nginx \
    net-tools htop iotop
```

---

## DAY 1: CORE INFRASTRUCTURE (8 HOURS)

### 1.1 Install K3s on Server 1
```bash
# Install K3s with embedded etcd for HA
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644

# Verify installation
sudo systemctl status k3s
kubectl get nodes

# Export kubeconfig for remote access
sudo cat /etc/rancher/k3s/k3s.yaml > ~/kubeconfig
# Edit server URL in kubeconfig to Server1's IP
```
**Purpose:** K3s provides lightweight Kubernetes for container orchestration with built-in high availability.

### 1.2 Install Docker on Server 2
```bash
# Add Docker repository
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker
docker run hello-world
```
**Purpose:** Docker enables containerized application deployment for non-Kubernetes workloads.

### 1.3 Setup Tailscale Mesh Network
```bash
# Install on Server 1
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Install on Server 2
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Note the Tailscale IPs for both servers
tailscale ip -4
```
**Purpose:** Tailscale creates secure, zero-config VPN mesh between servers without port forwarding.

### 1.4 Deploy LIMS Application
```bash
# On Server 1 - Create namespace
kubectl create namespace lims

# Deploy LIMS (create this file first)
cat > lims-deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lims-backend
  namespace: lims
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lims
  template:
    metadata:
      labels:
        app: lims
    spec:
      containers:
      - name: lims
        image: your-registry/lims:latest
        ports:
        - containerPort: 8080
        env:
        - name: FDA_COMPLIANCE
          value: "21_CFR_PART_11"
EOF

kubectl apply -f lims-deployment.yaml
```
**Purpose:** LIMS demonstrates FDA-compliant application deployment with audit trails.

---

## DAY 2: CI/CD PIPELINE SPLIT (8 HOURS)

### 2.1 Jenkins for LIMS (Server 1)
```bash
# Deploy Jenkins in K3s
kubectl create namespace jenkins

# Create Jenkins deployment
cat > jenkins.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins
  namespace: jenkins
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jenkins
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      containers:
      - name: jenkins
        image: jenkins/jenkins:lts
        ports:
        - containerPort: 8080
        - containerPort: 50000
        volumeMounts:
        - name: jenkins-data
          mountPath: /var/jenkins_home
      volumes:
      - name: jenkins-data
        hostPath:
          path: /var/jenkins
EOF

kubectl apply -f jenkins.yaml

# Get initial admin password
kubectl exec -n jenkins deploy/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword
```
**Purpose:** Jenkins provides FDA-compliant CI/CD with approval gates and audit trails.

### 2.2 ArgoCD for Pharma (Server 2)
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward for access
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
**Purpose:** ArgoCD enables GitOps deployment pattern for pharmaceutical GMP compliance.

### 2.3 Deploy Finance App (Docker on Server 1)
```bash
# On Server 1 - Deploy Finance app with Docker
cd apps/finance-trading

# Build and run with Docker Compose
docker-compose up -d

# Verify containers
docker ps
docker logs finance-trading-app

# Check health
curl http://localhost:8081/health
```
**Purpose:** Finance app demonstrates SOX-compliant trading system with transaction auditing.

### 2.4 Deploy Pharma App (Docker on Server 2)
```bash
# On Server 2 - Deploy Pharma app with Docker
cd apps/pharma-manufacturing

# Build and run with Docker Compose
docker-compose up -d

# Verify containers
docker ps
docker logs pharma-manufacturing-app

# Check health
curl http://localhost:8082/health
```
**Purpose:** Pharma app demonstrates GMP-compliant manufacturing system with GitOps via ArgoCD.

---

## DAY 3: MONITORING STACK (8 HOURS)

### 3.1 Prometheus + Grafana on Server 2
```bash
# Create monitoring stack with Docker Compose
cat > monitoring-stack.yaml <<EOF
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
EOF

docker-compose -f monitoring-stack.yaml up -d
```
**Purpose:** Prometheus collects metrics; Grafana visualizes them for system observability.

### 3.2 Loki for Logs (NOT Elasticsearch)
```bash
# Add Loki to monitoring stack
cat >> monitoring-stack.yaml <<EOF
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
EOF

# Create Promtail config
cat > promtail-config.yml <<EOF
server:
  http_listen_port: 9080
clients:
  - url: http://loki:3100/loki/api/v1/push
scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/*log
EOF

docker-compose -f monitoring-stack.yaml up -d
```
**Purpose:** Loki provides lightweight log aggregation, saving 3.5GB RAM vs Elasticsearch.

### 3.3 Configure Alertmanager
```bash
# Add Alertmanager configuration
cat > alertmanager.yml <<EOF
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://forensic-api:8888/webhook'
EOF

# Deploy Alertmanager
docker run -d -p 9093:9093 \
  -v $(pwd)/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager
```
**Purpose:** Alertmanager handles alerts from Prometheus and triggers forensic evidence collection.

---

## DAY 4: FORENSIC COLLECTOR - YOUR DIFFERENTIATOR (8 HOURS)

### 4.1 Build Forensic Collector Image
```bash
cd forensic-collector

# Build Docker image
docker build -t forensic-collector:latest -f docker/Dockerfile.forensic .

# Verify image
docker images | grep forensic
```
**Purpose:** Creates containerized forensic collector for evidence preservation.

### 4.2 Deploy to K3s Cluster
```bash
# Apply DaemonSet to monitor all nodes
kubectl apply -f kubernetes/forensic-collector-daemonset.yaml

# Verify deployment
kubectl get pods -n forensics
kubectl logs -n forensics daemonset/forensic-collector
```
**Purpose:** DaemonSet ensures forensic collector runs on every K3s node for complete coverage.

### 4.3 Configure Evidence Storage
```bash
# Create forensics directories on both servers
sudo mkdir -p /var/forensics/{evidence,reports}
sudo chown -R $USER:$USER /var/forensics

# Initialize evidence database
python3 scripts/forensic_collector.py verify
```
**Purpose:** Establishes secure evidence storage with cryptographic chain of custody.

### 4.4 Test Evidence Collection
```bash
# Trigger test incident
python3 scripts/forensic_collector.py capture test_incident lims HIGH

# Verify evidence chain
python3 scripts/forensic_collector.py verify

# Access web interface
kubectl port-forward -n forensics svc/forensic-api 8888:8888
# Browse to http://localhost:8888
```
**Purpose:** Validates forensic collection and cryptographic integrity verification.

---

## DAY 5: EC2 GATEWAY SETUP (8 HOURS)

### 5.1 Launch EC2 t2.micro
```bash
# Use AWS CLI or Console
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t2.micro \
  --key-name your-key \
  --security-groups your-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=forensic-gateway}]'

# SSH to instance
ssh -i your-key.pem ubuntu@ec2-public-ip
```
**Purpose:** EC2 provides public-facing gateway for demo access without exposing home network.

### 5.2 Install Tailscale on EC2
```bash
# On EC2 instance
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --accept-routes

# Join same network as servers
```
**Purpose:** Connects EC2 to private Tailscale mesh for secure backend access.

### 5.3 Configure Nginx Reverse Proxy
```bash
# Install Nginx
sudo apt install -y nginx

# Configure proxy
sudo cat > /etc/nginx/sites-available/default <<EOF
server {
    listen 80;
    
    location / {
        proxy_pass http://server2-tailscale:3000;  # Grafana
        proxy_set_header Host \$host;
    }
    
    location /forensics {
        proxy_pass http://server1-tailscale:8888;
        proxy_set_header Host \$host;
    }
    
    location /dr-status {
        proxy_pass http://server2-tailscale:8889;
        proxy_set_header Host \$host;
    }
}
EOF

sudo nginx -t
sudo systemctl reload nginx
```
**Purpose:** Nginx proxies requests to internal services via Tailscale without exposing them directly.

### 5.4 Create Public Status Page
```bash
# Create simple status page
cat > /var/www/html/index.html <<EOF
<!DOCTYPE html>
<html>
<head><title>DevOps Portfolio - Forensic Evidence System</title></head>
<body>
<h1>Production Infrastructure Status</h1>
<ul>
  <li><a href="/grafana">Grafana Dashboards</a></li>
  <li><a href="/forensics">Forensic Evidence Chain</a></li>
  <li><a href="/dr-status">Disaster Recovery Status</a></li>
</ul>
<p>Powered by Forensic Evidence Collector</p>
</body>
</html>
EOF
```
**Purpose:** Provides easy demo access points for interview presentation.

---

## DAY 6: DISASTER RECOVERY & DEMO PREP (8 HOURS)

### 6.1 Configure Automated Backups
```bash
# Add to crontab on Server 1
crontab -e
# Add these lines:
0 * * * * /home/ubuntu/scripts/backup-forensics.sh
0 2 * * * /home/ubuntu/scripts/backup-k3s.sh
*/5 * * * * rsync -av /var/forensics/ server2:/forensics-replica/
```
**Purpose:** Ensures continuous data protection with multiple backup layers.

### 6.2 Run Disaster Recovery Test (3 TIMES!)
```bash
# First test
./scripts/disaster-recovery-test.sh

# Review results
cat /home/ubuntu/DISASTER_RECOVERY_PROOF.txt

# Run twice more to ensure consistency
./scripts/disaster-recovery-test.sh
./scripts/disaster-recovery-test.sh
```
**Purpose:** Proves <30 minute recovery with zero data loss for interview credibility.

### 6.3 Create Demo Scenarios
```bash
# Pre-populate some incidents for demo
curl -X POST http://localhost:8888/trigger/lims
sleep 5
curl -X POST http://localhost:8888/trigger/finance
sleep 5
curl -X POST http://localhost:8888/trigger/pharma
```
**Purpose:** Ensures impressive evidence chain display during demo.

### 6.4 Practice Demo Flow
```bash
# 1. Open Evidence Viewer
open http://ec2-public-ip:8888

# 2. Show DR proof
cat DISASTER_RECOVERY_PROOF.txt

# 3. Trigger live incident
kubectl delete pod lims-backend-xxxxx

# 4. Show Grafana dashboards
open http://ec2-public-ip:3000

# 5. Verify chain integrity
curl http://localhost:8888/verify
```
**Purpose:** Rehearsal ensures smooth, confident presentation during interview.

---

## POST-DEPLOYMENT VERIFICATION

### System Health Checks
```bash
# K3s cluster
kubectl get nodes
kubectl get pods --all-namespaces

# Docker containers
docker ps

# Forensic collector
kubectl logs -n forensics daemonset/forensic-collector

# Evidence chain
python3 scripts/forensic_collector.py verify

# Backup verification
ls -la /backups/k3s/
ls -la /var/forensics/evidence/
```

### Performance Metrics
- K3s cluster recovery: <5 minutes
- Application deployment: <10 minutes  
- Evidence chain verification: <1 second
- Total DR time: <30 minutes
- Monthly cost: <$25

---

## TROUBLESHOOTING GUIDE

### K3s Issues
```bash
# Reset K3s if needed
sudo systemctl stop k3s
sudo k3s-killall.sh
sudo systemctl start k3s
```

### Docker Issues
```bash
# Clean Docker resources
docker system prune -a
docker volume prune
```

### Forensic Collector Issues
```bash
# Restart collector
kubectl rollout restart daemonset/forensic-collector -n forensics

# Check logs
kubectl logs -n forensics daemonset/forensic-collector --tail=100
```

### Network Issues
```bash
# Restart Tailscale
sudo tailscale down
sudo tailscale up
```

---

## INTERVIEW PREPARATION

### Key Talking Points
1. **Forensic methodology** - Applied crime scene preservation to DevOps
2. **Cryptographic chain** - Every incident cryptographically linked
3. **Compliance ready** - FDA, SOX, GMP evidence automatically preserved
4. **Cost optimized** - 95% savings vs cloud ($25 vs $500/month)
5. **Production tested** - 3+ successful disaster recovery tests

### Demo Script (5 minutes)
```
0:00 - Open Evidence Viewer
"Let me show you something unique - forensic evidence collection for DevOps"

0:30 - Show DR Test
"I've tested complete failure 3 times. Recovery in <30 min, zero data loss"

2:00 - Trigger Incident
"Watch real-time evidence capture..."

3:30 - Architecture Overview  
"Monitors 3 production apps with different compliance requirements"

4:30 - Closing
"This combines my forensic science background with DevOps innovation"
```

### Expected Questions & Answers
**Q: "Why forensic collection?"**
A: "In production, you get one chance to capture evidence. This ensures we never lose critical debugging information."

**Q: "How is this different from logging?"**
A: "Logs show events. This preserves complete system state with legal-grade chain of custody."

**Q: "What's the business value?"**
A: "Reduces MTTR, satisfies auditors instantly, and provides irrefutable evidence for post-mortems."

---

## SUCCESS CRITERIA

- [ ] All 3 applications deployed and healthy
- [ ] Forensic collector capturing incidents  
- [ ] Evidence chain cryptographically verified
- [ ] Disaster recovery <30 minutes achieved
- [ ] Demo practiced 10+ times
- [ ] EC2 gateway accessible
- [ ] Costs under $25/month
- [ ] GitHub repository updated
- [ ] Video demonstration recorded

---

## NEXT STEPS

1. Complete deployment following this guide
2. Run DR test 3+ times
3. Practice demo until smooth
4. Record video backup
5. Update LinkedIn with project
6. Prepare 30-second elevator pitch
7. Schedule mock interviews

---

**Remember:** The Forensic Evidence Collector is your differentiator. No other candidate has this. Focus your demo on this unique innovation that came from YOUR background, not a tutorial.

Good luck with your deployment and interview!