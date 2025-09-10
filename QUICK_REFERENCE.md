# QUICK REFERENCE - ESSENTIAL COMMANDS
## Zero-Downtime Pipeline with Forensic Evidence Collector

---

## 🚀 DEPLOYMENT COMMANDS

### Initial Setup
```bash
# Install K3s (Server 1)
curl -sfL https://get.k3s.io | sh -

# Install Docker (Server 2)
curl -fsSL https://get.docker.com | sh

# Install Tailscale (Both servers)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Build & Deploy Forensic Collector
```bash
# Build image
docker build -t forensic-collector:latest -f forensic-collector/docker/Dockerfile.forensic .

# Deploy to K3s
kubectl apply -f forensic-collector/kubernetes/forensic-collector-daemonset.yaml

# Check status
kubectl get pods -n forensics
```

---

## 🔬 FORENSIC EVIDENCE COMMANDS

### Capture Evidence
```bash
# Manual incident capture
python3 scripts/forensic_collector.py capture <type> <application> [severity]

# Examples
python3 scripts/forensic_collector.py capture crash lims CRITICAL
python3 scripts/forensic_collector.py capture memory_leak finance HIGH
python3 scripts/forensic_collector.py capture compliance_violation pharma CRITICAL
```

### Verify Evidence Chain
```bash
# Verify entire chain
python3 scripts/forensic_collector.py verify

# Verify specific incident
python3 scripts/forensic_collector.py verify INC-20240108-143022
```

### Access Web Interface
```bash
# Port forward to local
kubectl port-forward -n forensics svc/forensic-api 8888:8888

# Open in browser
open http://localhost:8888
```

### Trigger Demo Incidents
```bash
# FDA violation (LIMS)
curl -X POST http://localhost:8888/trigger/lims

# SOX alert (Finance)
curl -X POST http://localhost:8888/trigger/finance  

# GMP breach (Pharma)
curl -X POST http://localhost:8888/trigger/pharma

# DR test
curl -X POST http://localhost:8888/trigger/dr_test
```

---

## 🏥 DISASTER RECOVERY

### Run DR Test
```bash
# Full disaster recovery test
./scripts/disaster-recovery-test.sh

# View proof
cat /home/ubuntu/DISASTER_RECOVERY_PROOF.txt
```

### Backup Commands
```bash
# K3s cluster backup
./scripts/backup-k3s.sh

# Forensic evidence backup
./scripts/backup-forensics.sh

# Manual K3s snapshot
sudo k3s etcd-snapshot save --name manual-backup

# Restore K3s from backup
sudo k3s etcd-snapshot restore /backups/k3s/k3s-backup-LATEST
```

---

## 📊 MONITORING & LOGS

### Prometheus
```bash
# Port forward
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Check targets
curl http://localhost:9090/api/v1/targets
```

### Grafana
```bash
# Port forward
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Default login: admin/admin
```

### Logs
```bash
# K3s pod logs
kubectl logs -n <namespace> <pod-name> --tail=100 -f

# Docker logs
docker logs <container-name> --tail=100 -f

# Forensic collector logs
kubectl logs -n forensics daemonset/forensic-collector --tail=100
```

---

## 🚢 KUBERNETES (K3s)

### Deployments
```bash
# List all resources
kubectl get all --all-namespaces

# Apply configuration
kubectl apply -f <file.yaml>

# Delete resource
kubectl delete -f <file.yaml>

# Scale deployment
kubectl scale deployment <name> --replicas=3

# Rollout restart
kubectl rollout restart deployment/<name>

# Get pod details
kubectl describe pod <pod-name>

# Execute in pod
kubectl exec -it <pod-name> -- /bin/bash
```

### Troubleshooting
```bash
# Get events
kubectl get events --sort-by='.lastTimestamp'

# Check node status
kubectl get nodes -o wide

# Resource usage
kubectl top nodes
kubectl top pods --all-namespaces
```

---

## 🐳 DOCKER

### Container Management
```bash
# List containers
docker ps -a

# Start/stop/restart
docker start <container>
docker stop <container>
docker restart <container>

# Remove container
docker rm <container>

# View logs
docker logs <container> --tail=100 -f
```

### Image Management
```bash
# List images
docker images

# Build image
docker build -t <name>:<tag> .

# Remove image
docker rmi <image>

# Clean everything
docker system prune -a --volumes
```

### Docker Compose
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build
```

---

## 🌐 NETWORKING

### Tailscale
```bash
# Status
tailscale status

# Get IP
tailscale ip -4

# Ping test
tailscale ping <hostname>

# Restart
sudo tailscale down
sudo tailscale up
```

### Port Forwarding
```bash
# K8s port forward
kubectl port-forward svc/<service> <local>:<remote>

# SSH tunnel
ssh -L <local>:<remote-host>:<remote-port> user@server
```

### Network Debugging
```bash
# Test connectivity
curl -v http://localhost:8080/health

# Check ports
netstat -tulpn | grep <port>

# DNS lookup
nslookup <hostname>
dig <hostname>
```

---

## 📦 APPLICATION SPECIFIC

### LIMS (FDA Compliant)
```bash
# Check compliance status
curl http://localhost:8080/api/compliance/fda

# View audit trail
kubectl exec -n lims deploy/lims-backend -- cat /var/log/audit.log
```

### Finance Trading
```bash
# Check SOX compliance
curl http://localhost:8081/api/compliance/sox

# View transactions
docker exec finance-db psql -U finance -c "SELECT * FROM transactions LIMIT 10;"
```

### Pharma Manufacturing
```bash
# Check GMP status
curl http://localhost:8082/api/compliance/gmp

# View production metrics
kubectl logs -n pharma deployment/pharma-app | grep "PRODUCTION"
```

---

## 🛠️ MAINTENANCE

### System Updates
```bash
# Update K3s
curl -sfL https://get.k3s.io | sh -

# Update Docker
sudo apt update && sudo apt upgrade docker-ce

# Update forensic collector
docker pull forensic-collector:latest
kubectl rollout restart daemonset/forensic-collector -n forensics
```

### Resource Cleanup
```bash
# Clean K8s resources
kubectl delete pods --field-selector status.phase=Failed --all-namespaces

# Clean Docker
docker container prune -f
docker image prune -f
docker volume prune -f

# Clean logs
journalctl --vacuum-time=7d
```

---

## 🎭 DEMO COMMANDS

### Interview Demo Flow
```bash
# 1. Open Evidence Viewer
open http://ec2-public-ip:8888

# 2. Show DR proof
cat /home/ubuntu/DISASTER_RECOVERY_PROOF.txt

# 3. Trigger incident
kubectl delete pod lims-backend-xxxxx

# 4. Verify chain
curl http://localhost:8888/verify

# 5. Show dashboards
open http://ec2-public-ip:3000
```

### Quick Status Check
```bash
# One-liner health check
echo "K3s:" && kubectl get nodes && echo "Docker:" && docker ps --format "table {{.Names}}\t{{.Status}}" && echo "Forensics:" && python3 scripts/forensic_collector.py verify
```

---

## 🚨 EMERGENCY PROCEDURES

### System Down
```bash
# Quick recovery
sudo systemctl restart k3s
docker-compose restart
sudo systemctl restart nginx
```

### Evidence Chain Broken
```bash
# Restore from backup
cp /backups/forensics/chain_latest.db /var/forensics/chain_of_custody.db
python3 scripts/forensic_collector.py verify
```

### Out of Resources
```bash
# Free up space
docker system prune -a --volumes -f
kubectl delete pods --field-selector status.phase=Succeeded --all-namespaces
sudo journalctl --vacuum-size=100M
```

---

## 📝 CONFIGURATION FILES

### Key File Locations
```bash
/etc/rancher/k3s/k3s.yaml          # K3s config
/var/lib/rancher/k3s/              # K3s data
/var/forensics/                    # Evidence storage
/backups/                           # Backup location
~/kubeconfig                        # Kubectl config
docker-compose.yml                  # Docker services
```

### Environment Variables
```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
export DOCKER_HOST=unix:///var/run/docker.sock
export FORENSICS_DIR=/var/forensics
```

---

## 💰 COST MONITORING

```bash
# Check EC2 usage
aws ec2 describe-instances --instance-ids <id> --query 'Reservations[0].Instances[0].{Type:InstanceType,State:State.Name}'

# Check resource usage
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "Memory: $(free -h | awk '/^Mem/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2}')"
```

---

## 🔗 USEFUL ALIASES

Add to ~/.bashrc:
```bash
# Kubernetes
alias k='kubectl'
alias kgp='kubectl get pods --all-namespaces'
alias kgs='kubectl get svc --all-namespaces'
alias kaf='kubectl apply -f'
alias kdel='kubectl delete -f'
alias klog='kubectl logs -f'

# Docker
alias d='docker'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dlog='docker logs --tail=100 -f'
alias dprune='docker system prune -a -f'

# Forensics
alias fcap='python3 scripts/forensic_collector.py capture'
alias fver='python3 scripts/forensic_collector.py verify'
alias fweb='kubectl port-forward -n forensics svc/forensic-api 8888:8888'

# Quick checks
alias health='echo "=== System Health ===" && kubectl get nodes && docker ps && python3 scripts/forensic_collector.py verify'
alias backup='./scripts/backup-k3s.sh && ./scripts/backup-forensics.sh'
```

---

## 📞 INTERVIEW READY COMMANDS

```bash
# The Money Shot - Evidence Viewer
open http://ec2-public-ip:8888

# The Proof - DR Test
cat /home/ubuntu/DISASTER_RECOVERY_PROOF.txt | head -20

# The Demo - Live Incident
kubectl delete pod $(kubectl get pods -n lims -o name | head -1)

# The Innovation - Chain Verification  
curl -s http://localhost:8888/verify | jq .

# The Value - Cost Savings
echo "Monthly cost: \$25 vs Cloud: \$500 (95% savings)"
```

---

**Remember:** Focus on the Forensic Evidence Collector during your demo. It's YOUR unique innovation that no tutorial teaches!