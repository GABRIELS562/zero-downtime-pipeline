#!/bin/bash

# Tailscale Setup for Portfolio Access
echo "🔒 Setting up Tailscale for secure portfolio access..."

# Install Tailscale on your server
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up

# Get your Tailscale IP
echo "Your Tailscale IP:"
tailscale ip -4

# Configure Tailscale to serve your app
sudo tailscale serve https / http://localhost:80

echo "✅ Access your portfolio at:"
echo "   https://$(tailscale ip -4)"
echo "   or"
echo "   https://your-machine-name.tailnet-name.ts.net"

# During interview, you can:
# 1. Share the Tailscale link
# 2. Add interviewer's email to your Tailnet temporarily
# 3. Or screen share with live demo