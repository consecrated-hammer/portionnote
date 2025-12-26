#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

docker compose --env-file .env.dev -f docker-compose.traefik.dev.yml up -d --build --force-recreate --remove-orphans

docker logs portionnote-dev -f
