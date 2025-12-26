#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

cd "${FRONTEND_DIR}"

if [[ "${SKIP_NPM_INSTALL:-0}" != "1" ]] && [[ ! -x "node_modules/.bin/vite" ]]; then
  npm install
fi

export VITE_API_BASE_URL="${VITE_API_BASE_URL:-/}"
export VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://localhost:8000}"

if [[ "${1:-}" == "test" ]]; then
  exec npm test -- "${@:2}"
fi

npm run dev -- --host 0.0.0.0 --port "${WEB_PORT:-5173}"
