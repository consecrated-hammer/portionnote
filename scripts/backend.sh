#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
DATA_DIR="${BACKEND_DIR}/.data"
VENV_DIR="${BACKEND_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

cd "${BACKEND_DIR}"

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  rm -rf "${VENV_DIR}"
  if ! "${PYTHON_BIN}" -m venv "${VENV_DIR}"; then
    echo "Failed to create virtualenv. On Debian/Ubuntu install python3-venv." >&2
    exit 1
  fi
fi

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "Virtualenv is missing ${VENV_DIR}/bin/activate. Remove ${VENV_DIR} and try again." >&2
  exit 1
fi

source "${VENV_DIR}/bin/activate"

VENV_PYTHON="${VENV_DIR}/bin/python"
if [[ ! -x "${VENV_PYTHON}" ]]; then
  VENV_PYTHON="${VENV_DIR}/bin/python3"
fi
if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Virtualenv python not found in ${VENV_DIR}/bin. Remove ${VENV_DIR} and try again." >&2
  exit 1
fi

if [[ "${SKIP_PIP_INSTALL:-0}" != "1" ]]; then
  "${VENV_PYTHON}" -m pip install -r requirements.txt
fi

mkdir -p "${DATA_DIR}"

export DATABASE_FILE="${DATABASE_FILE:-${DATA_DIR}/portionnote.sqlite}"
export WEB_ORIGIN="${WEB_ORIGIN:-http://localhost:5173}"

if [[ "${1:-}" == "test" ]]; then
  exec pytest "${@:2}"
fi

exec "${VENV_PYTHON}" -m uvicorn app.main:App --reload --host 0.0.0.0 --port "${API_PORT:-8002}"
