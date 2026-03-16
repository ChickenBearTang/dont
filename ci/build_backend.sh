#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[build_backend] Building backend"
bash "${REPO_ROOT}/backend/gradlew" -p "${REPO_ROOT}/backend" clean test build

echo "[build_backend] Done"
