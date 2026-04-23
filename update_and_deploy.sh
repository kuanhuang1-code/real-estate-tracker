#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

python3 -m unittest discover -s tests -v
python3 scripts/update_tracker.py

if ! git diff --quiet -- index.html; then
  git add index.html
  git commit -m "chore: refresh Zillow housing data"
  git push origin HEAD:main
  git push origin HEAD:gh-pages --force
else
  echo "No tracker data changes detected."
fi
