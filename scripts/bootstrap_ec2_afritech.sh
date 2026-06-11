#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Run this script as the Ubuntu app user, not as root."
  exit 1
fi

APP_DIR="${1:-$HOME/afritelematics}"

echo "==> AfriTech EC2 bootstrap"
echo "App directory: $APP_DIR"

echo "==> Installing Docker, Compose plugin, git, and firewall tooling"
sudo apt update -y
sudo apt install -y ca-certificates curl git docker.io docker-compose-v2 ufw

echo "==> Enabling Docker"
sudo systemctl enable --now docker

if ! groups "${USER}" | grep -q '\bdocker\b'; then
  echo "==> Adding ${USER} to docker group"
  sudo usermod -aG docker "${USER}"
  DOCKER_GROUP_ADDED=1
else
  DOCKER_GROUP_ADDED=0
fi

echo "==> Opening HTTP/HTTPS through UFW"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "==> Preparing application directory"
mkdir -p "${APP_DIR}"

cat <<EOF

Bootstrap complete.

Next steps:

1. If the machine was just upgraded to a new kernel, reboot first:
   sudo reboot

2. Reconnect and refresh docker group membership:
   ssh -i ~/.ssh/<your-key>.pem ubuntu@<your-host>
   cd ${APP_DIR}

3. Put the repository in place:
   git clone <your-repo-url> ${APP_DIR}
   or rsync/copy the existing repo into ${APP_DIR}

4. Configure production secrets:
   cd ${APP_DIR}/deploy/production
   cp .env.production.example .env.production
   nano .env.production

5. Place signing keys on the host:
   sudo mkdir -p /run/secrets
   sudo cp /path/to/afritech_private_key.pem /run/secrets/afritech_private_key.pem
   sudo cp /path/to/afritech_public_key.pem /run/secrets/afritech_public_key.pem
   sudo chmod 600 /run/secrets/afritech_private_key.pem
   sudo chmod 644 /run/secrets/afritech_public_key.pem

6. Start the production stack:
   cd ${APP_DIR}
   ./scripts/deploy_production_compose.sh --base-url https://<your-domain>

7. Verify the live service:
   ./scripts/run_local_production_probe.sh https://<your-domain>

EOF

if [[ "${DOCKER_GROUP_ADDED}" -eq 1 ]]; then
  echo "Docker group membership was updated. Log out and back in after any reboot before running docker compose."
fi
