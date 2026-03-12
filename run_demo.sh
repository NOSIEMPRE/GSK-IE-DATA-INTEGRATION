#!/usr/bin/env bash
set -euo pipefail

# RWD TrustChain — One-click demo
# Runs: download → load → validate → anchor → dashboard
#
# Usage:
#   bash run_demo.sh           # full pipeline + open dashboard
#   bash run_demo.sh --no-ui   # pipeline only, no Streamlit
#   bash run_demo.sh --mlflow  # log validation+anchor to MLflow (scenario1 by default)
#   bash run_demo.sh --pprl    # run PPRL multi-source linkage demo

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_ROOT}"

NO_UI=false
USE_MLFLOW=false
USE_PPRL=false
for arg in "$@"; do
  [[ "$arg" == "--no-ui" ]] && NO_UI=true
  [[ "$arg" == "--mlflow" ]] && USE_MLFLOW=true
  [[ "$arg" == "--pprl" ]] && USE_PPRL=true
done

echo "=== RWD TrustChain Demo ==="

# 1. Download (skip if data exists)
if [[ ! -d "data/synthea1k" ]] || [[ -z "$(ls -A data/synthea1k 2>/dev/null)" ]]; then
  echo "[1/5] Downloading Synthea OMOP 1k..."
  bash 01-initial-notebook/download_synthea_omop.sh
else
  echo "[1/5] data/synthea1k exists, skipping download"
fi

# 2. Load into DuckDB
echo "[2/5] Loading into DuckDB..."
python 01-initial-notebook/load_synthea_duckdb.py

# 3–4. Quality validation + hash anchoring (optionally with MLflow)
if [[ "$USE_MLFLOW" == "true" ]]; then
  echo "[3–4/5] Running validation + anchoring with MLflow tracking..."
  python 03-experiment-tracking/run_with_mlflow.py
  # For scenario2: python 03-experiment-tracking/run_with_mlflow.py --scenario scenario2
else
  echo "[3/5] Running quality validation..."
  python 02-data-sampling-feature/validate_omop_quality.py
  echo "[4/5] Hash anchoring..."
  python 03-experiment-tracking/anchor_hashes.py
fi

# 4b. PPRL multi-source linkage demo (optional)
if [[ "$USE_PPRL" == "true" ]]; then
  echo "[4b/5] PPRL multi-source linkage demo..."
  python 02-data-sampling-feature/pprl_multi_source_demo.py
  python 03-experiment-tracking/anchor_hashes.py
fi

# 5. Dashboard
if [[ "$NO_UI" == "true" ]]; then
  echo "[5/5] Skipping dashboard (--no-ui)"
  echo "Done. Run: streamlit run 04-deployment/app.py"
else
  echo "[5/5] Starting Governance Dashboard..."
  streamlit run 04-deployment/app.py
fi
