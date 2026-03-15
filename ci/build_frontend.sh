#!/usr/bin/env bash
set -euo pipefail

echo "[build_frontend] Installing dependencies"
npm --prefix frontend install

echo "[build_frontend] Running lint"
npm --prefix frontend run lint

echo "[build_frontend] Building frontend"
npm --prefix frontend run build

echo "[build_frontend] Done"
