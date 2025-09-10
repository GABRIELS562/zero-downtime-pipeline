#!/bin/bash

# Cloudflare Tunnel Setup - FREE public access without opening ports!
echo "🌐 Setting up Cloudflare Tunnel for public access..."

# Install cloudflared
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Quick tunnel (no account needed - temporary URL)
cloudflared tunnel --url http://localhost:80

# OR for permanent tunnel with your domain:
# 1. Login to Cloudflare
cloudflared tunnel login

# 2. Create tunnel
cloudflared tunnel create devops-portfolio

# 3. Route traffic
cloudflared tunnel route dns devops-portfolio portfolio.yourdomain.com

# 4. Create config file
cat > ~/.cloudflared/config.yml <<EOF
tunnel: devops-portfolio
credentials-file: /home/$USER/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: portfolio.yourdomain.com
    service: http://localhost:80
  - hostname: api.portfolio.yourdomain.com
    path: /finance/*
    service: http://localhost:8080
  - hostname: api.portfolio.yourdomain.com
    path: /pharma/*
    service: http://localhost:8000
  - service: http_status:404
EOF

# 5. Run tunnel
cloudflared tunnel run devops-portfolio