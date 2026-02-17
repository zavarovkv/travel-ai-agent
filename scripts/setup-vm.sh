#!/usr/bin/env bash
set -euo pipefail

echo "=== Installing Docker ==="
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "=== Adding current user to docker group ==="
sudo usermod -aG docker "$USER"

echo "=== Cloning repository ==="
REPO_URL="${1:?Usage: setup-vm.sh <github-repo-url>}"
cd ~
git clone "$REPO_URL" travel-ai-agent
cd travel-ai-agent

echo "=== Setup complete ==="
echo "1. Create .env file: cp .env.example .env && nano .env"
echo "2. Re-login for docker group to take effect, then run: docker compose up -d"
