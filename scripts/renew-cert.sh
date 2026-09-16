#!/bin/bash
# renew-cert.sh — Renew Let's Encrypt TLS certificate via Certbot.
# Run via cron: 0 3 * * 1 /home/ec2-user/Pacman-Game/scripts/renew-cert.sh

set -euo pipefail

echo "=== Certificate renewal started at $(date -u) ==="

cd /home/ec2-user/Pacman-Game

# Run certbot renewal via Docker Compose
docker compose run --rm certbot renew --webroot -w /var/www/certbot

# Reload Nginx to pick up new certificates
docker compose exec nginx nginx -s reload

echo "=== Certificate renewal completed at $(date -u) ==="
