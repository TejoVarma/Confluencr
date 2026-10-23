#!/usr/bin/env bash
# Builds a Beanstalk-ready zip (files at the zip root, no secrets/venv/tests).
# Usage: ./scripts/package.sh  ->  dist/backend-<timestamp>.zip
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p dist
out="dist/backend-$(date +%Y%m%d-%H%M%S).zip"
zip -rq "$out" app Procfile requirements.txt .ebextensions -x '*__pycache__*' '*.pyc'
echo "Created $out"
zipinfo -1 "$out" | sed "s/^/  /"
