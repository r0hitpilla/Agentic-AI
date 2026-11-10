#!/usr/bin/env bash
# Validate everything in the repo: tests, schemas, examples, OpenAPI, generated docs, Mermaid diagrams.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pip install -q -r requirements-dev.txt
python3 scripts/render_scenarios.py --check
python3 -m pytest -q
if command -v node >/dev/null 2>&1; then
  (cd scripts/mermaid-check && npm install --silent --no-audit --no-fund)
  node scripts/mermaid-check/check.mjs README.md docs/*.md knowledge/README.md
else
  echo "node not found: skipping Mermaid parse check"
fi
