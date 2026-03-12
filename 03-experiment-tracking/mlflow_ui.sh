#!/usr/bin/env bash
# Launch MLflow UI with explicit backend store (works from any directory)
# Usage: bash 03-experiment-tracking/mlflow_ui.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MLRUNS="$PROJECT_ROOT/mlruns"

echo "MLflow UI: http://localhost:5000"
echo "Backend:   $MLRUNS"
echo "Experiment: rwd-trustchain-quality"
exec mlflow ui --backend-store-uri "file://${MLRUNS}"
