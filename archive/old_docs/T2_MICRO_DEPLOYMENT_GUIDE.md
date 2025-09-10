# 🚀 T2.MICRO DEPLOYMENT GUIDE - Zero-Downtime Pipeline

## ⚠️ Critical Constraints
- **RAM**: Only 1GB (need ~600MB free for OS)
- **CPU**: 1 vCPU (shared, burstable)
- **Storage**: 8-30GB typical
- **Network**: Limited bandwidth

## 📋 Deployment Strategy
We'll deploy a **minimal showcase version** with:
- Single container rotating between apps (not simultaneous)
- SQLite instead of PostgreSQL
- Basic monitoring only
- Static frontend served by Nginx

---

## PHASE 1: EC2 INSTANCE PREPARATION

### Step 1: Connect to Your EC2 Instance
```bash
# Connect via SSH (replace with your instance details)
ssh -i your-key.pem ec2-user@your-instance-ip

# Explanation:
# -i: Specifies your private key file for authentication
# ec2-user: Default username for Amazon Linux 2
# your-instance-ip: Public IP of your t2.micro instance
```

### Step 2: Update System & Install Prerequisites
```bash
# Update system packages for security patches
sudo yum update -y

# Explanation:
# yum: Package manager for Amazon Linux
# update: Updates all installed packages
# -y: Automatically answers "yes" to prompts

# Install Docker
sudo yum install docker -y

# Explanation:
# Installs Docker container runtime
# Essential for running our containerized applications

# Install Git for cloning repository
sudo yum install git -y

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Explanation:
# curl -L: Downloads file following redirects
# $(uname -s): Inserts system name (Linux)
# $(uname -m): Inserts machine architecture (x86_64)
# -o: Outputs to specified location

# Make Docker Compose executable
sudo chmod +x /usr/local/bin/docker-compose

# Explanation:
# chmod +x: Adds execute permission
# Allows the file to be run as a program

# Start Docker service
sudo systemctl start docker

# Explanation:
# systemctl: System service manager
# start docker: Initiates Docker daemon

# Enable Docker to start on boot
sudo systemctl enable docker

# Explanation:
# enable: Configures service to start automatically
# Ensures Docker runs after system reboot

# Add ec2-user to docker group (avoid using sudo)
sudo usermod -aG docker ec2-user

# Explanation:
# usermod: Modifies user account
# -aG docker: Appends user to docker group
# Allows running Docker without sudo

# Apply group changes (logout/login alternative)
newgrp docker

# Explanation:
# newgrp: Changes current group ID during login session
# Activates docker group membership immediately
```

### Step 3: Configure Swap (Critical for t2.micro!)
```bash
# Create 2GB swap file (essential for 1GB RAM)
sudo dd if=/dev/zero of=/swapfile bs=128M count=16

# Explanation:
# dd: Data duplicator command
# if=/dev/zero: Input file (produces zeros)
# of=/swapfile: Output file location
# bs=128M: Block size of 128 megabytes
# count=16: Number of blocks (128M × 16 = 2GB)

# Set swap file permissions
sudo chmod 600 /swapfile

# Explanation:
# chmod 600: Read/write for owner only
# Secures swap file from unauthorized access

# Set up swap area
sudo mkswap /swapfile

# Explanation:
# mkswap: Creates swap area in file
# Formats file for use as virtual memory

# Enable swap
sudo swapon /swapfile

# Explanation:
# swapon: Activates swap space
# System can now use file as virtual RAM

# Make swap permanent
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab

# Explanation:
# echo: Outputs swap configuration line
# tee -a: Appends to file while showing output
# /etc/fstab: File system table (mount configuration)
# Ensures swap activates on reboot

# Verify swap is active
free -h

# Explanation:
# free: Displays memory usage
# -h: Human-readable format (GB/MB)
# Should show 2GB swap available
```

---

## PHASE 2: REPOSITORY & CONFIGURATION

### Step 4: Clone Repository
```bash
# Clone your repository
git clone https://github.com/yourusername/zero-downtime-pipeline.git

# Explanation:
# git clone: Creates local copy of repository
# Downloads all code, configurations, and history

# Navigate to project directory
cd zero-downtime-pipeline

# Explanation:
# cd: Change directory command
# Moves into the cloned project folder
```

### Step 5: Set Permissions
```bash
# Make deployment script executable
chmod +x deploy-t2micro.sh

# Explanation:
# chmod +x: Adds execute permission
# Allows script to be run as ./deploy-t2micro.sh
```

---

## PHASE 3: GRADUAL DEPLOYMENT

### Step 6: Deploy Frontend First (Minimal Resources)
```bash
# Start with frontend only (50MB RAM)
./deploy-t2micro.sh frontend

# Explanation:
# Deploys only Nginx frontend server
# Uses minimal resources (50MB)
# Serves static HTML/JS files
# Sets up reverse proxy for APIs

# Verify frontend is running
docker ps

# Explanation:
# docker ps: Shows running containers
# Should show 'frontend' container
# Status should be 'Up' and 'healthy'

# Check memory usage
docker stats --no-stream

# Explanation:
# docker stats: Shows container resource usage
# --no-stream: Shows snapshot instead of live feed
# Monitor RAM usage stays under limits
```

### Step 7: Deploy Finance Trading App
```bash
# Deploy finance app (300MB RAM)
./deploy-t2micro.sh finance

# Explanation:
# Stops previous services to free memory
# Builds Finance Trading Docker image
# Starts frontend + finance containers
# Total usage: ~350MB RAM

# Test finance app health
curl http://localhost:8080/health

# Explanation:
# curl: Command-line HTTP client
# Tests health endpoint
# Should return JSON with "status": "healthy"

# Check application logs
docker logs finance-app --tail 50

# Explanation:
# docker logs: Shows container output
# --tail 50: Shows last 50 lines only
# Look for startup confirmation messages
```

### Step 8: Alternative - Deploy Pharma App
```bash
# OR deploy pharma instead (can't run both on t2.micro)
./deploy-t2micro.sh pharma

# Explanation:
# Alternative to finance deployment
# Pharma app also uses 300MB RAM
# Choose one app at a time for demo

# Verify pharma health
curl http://localhost:8090/health

# Explanation:
# Tests pharma app health endpoint
# Returns compliance status
# FDA validation checks included
```

### Step 9: Deploy Monitoring (Optional)
```bash
# Add minimal monitoring (180MB RAM)
./deploy-t2micro.sh monitoring

# Explanation:
# Adds Prometheus + Node Exporter
# Collects system and app metrics
# Only if sufficient memory available

# Access Prometheus
curl http://localhost:9090/-/healthy

# Explanation:
# Tests Prometheus health endpoint
# Confirms metrics collection active
# Access UI at http://your-ip:9090
```

---

## PHASE 4: SECURITY & ACCESS

### Step 10: Configure Security Groups
```bash
# In AWS Console or CLI, ensure these ports are open:
# Port 80: HTTP (Frontend)
# Port 443: HTTPS (Frontend) 
# Port 8080: Finance API (Demo)
# Port 8090: Pharma API (Demo)
# Port 9090: Prometheus (Optional)
# Port 22: SSH (Your IP only)

# Using AWS CLI:
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Explanation:
# authorize-security-group-ingress: Opens firewall port
# --protocol tcp: TCP traffic
# --port 80: HTTP port
# --cidr 0.0.0.0/0: Allow from anywhere (demo only)
```

### Step 11: Set Up Domain (Optional)
```bash
# Get your public IP
PUBLIC_IP=$(curl -s ifconfig.me)
echo "Your server IP: $PUBLIC_IP"

# Explanation:
# curl ifconfig.me: Returns public IP
# Use this IP to access your application
# Or configure Route53/DNS to point here
```

---

## PHASE 5: MONITORING & MAINTENANCE

### Step 12: Monitor Resources
```bash
# Real-time resource monitoring
docker stats

# Explanation:
# Shows live CPU/Memory usage
# Press Ctrl+C to exit
# Keep memory under 80% for stability

# Check disk usage
df -h

# Explanation:
# df: Disk free command
# -h: Human-readable sizes
# Monitor /dev/xvda1 usage

# View all logs
./deploy-t2micro.sh logs

# Explanation:
# Shows combined logs from all services
# Useful for debugging issues
```

### Step 13: Cleanup & Optimization
```bash
# Remove unused images (free space)
docker image prune -a

# Explanation:
# Removes all unused Docker images
# -a: Remove all unused, not just dangling
# Frees significant disk space

# Clean build cache
docker builder prune

# Explanation:
# Removes build cache
# Frees space from image builds

# Full system cleanup (careful!)
docker system prune -a --volumes

# Explanation:
# Removes all unused resources
# --volumes: Also removes unused volumes
# Warning: Deletes all stopped containers
```

---

## TROUBLESHOOTING GUIDE

### Common Issues & Solutions:

**1. Out of Memory Error**
```bash
# Solution: Increase swap
sudo dd if=/dev/zero of=/swapfile2 bs=128M count=8
sudo mkswap /swapfile2
sudo swapon /swapfile2

# Or stop unnecessary services
./deploy-t2micro.sh stop
./deploy-t2micro.sh frontend  # Start minimal
```

**2. Container Keeps Restarting**
```bash
# Check logs
docker logs [container-name] --tail 100

# Common fixes:
# - Reduce worker count to 1
# - Increase memory limits
# - Check database connections
```

**3. Slow Performance**
```bash
# Check CPU credits (t2.micro specific)
aws ec2 describe-instances --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].CpuOptions'

# Monitor burst balance in CloudWatch
```

---

## DEPLOYMENT MODES SUMMARY

| Mode | Command | RAM Usage | Services |
|------|---------|-----------|----------|
| **Minimal** | `./deploy-t2micro.sh frontend` | 50MB | Static frontend only |
| **Finance Demo** | `./deploy-t2micro.sh finance` | 350MB | Frontend + Finance API |
| **Pharma Demo** | `./deploy-t2micro.sh pharma` | 350MB | Frontend + Pharma API |
| **Monitoring** | `./deploy-t2micro.sh monitoring` | +180MB | Add Prometheus |
| **Status** | `./deploy-t2micro.sh status` | - | Show running services |
| **Stop All** | `./deploy-t2micro.sh stop` | - | Stop everything |

---

## POST-DEPLOYMENT VALIDATION

```bash
# Final validation checklist
echo "=== Deployment Validation ==="

# 1. Check all services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Test endpoints
PUBLIC_IP=$(curl -s ifconfig.me)
echo "Testing http://$PUBLIC_IP ..."
curl -I http://$PUBLIC_IP

# 3. Check resource usage
free -h
df -h
docker stats --no-stream

# 4. Verify logs are clean
docker-compose -f docker-compose.t2micro.yml logs --tail=10

echo "=== Deployment Complete ==="
```

---

## 🎯 QUICK START COMMANDS

For immediate deployment, run these commands on your t2.micro:

```bash
# 1. Quick setup (copy-paste all)
sudo yum update -y && \
sudo yum install -y docker git && \
sudo systemctl start docker && \
sudo systemctl enable docker && \
sudo usermod -aG docker ec2-user && \
sudo dd if=/dev/zero of=/swapfile bs=128M count=16 && \
sudo chmod 600 /swapfile && \
sudo mkswap /swapfile && \
sudo swapon /swapfile && \
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clone and deploy
git clone https://github.com/yourusername/zero-downtime-pipeline.git && \
cd zero-downtime-pipeline && \
chmod +x deploy-t2micro.sh && \
./deploy-t2micro.sh frontend
```

Your application will be accessible at `http://your-ec2-public-ip` within 5 minutes!