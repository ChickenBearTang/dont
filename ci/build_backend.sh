#!/usr/bin/env bash
set -euo pipefail

echo "[build_backend] Building backend"
./gradlew -p backend clean test build

echo "[build_backend] Done"
