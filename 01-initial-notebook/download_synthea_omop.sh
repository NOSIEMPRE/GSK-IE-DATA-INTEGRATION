#!/usr/bin/env bash
set -euo pipefail

# Download Synthea OMOP data (1k cohort) into the local data folder.
# Usage:
#   bash 01-initial-notebook/download_synthea_omop.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data/synthea1k"

mkdir -p "${DATA_DIR}"

echo "Downloading Synthea OMOP 1k dataset into: ${DATA_DIR}"
aws s3 cp --no-sign-request s3://synthea-omop/synthea1k/ "${DATA_DIR}/" --recursive

echo "Done. Example files:"
ls "${DATA_DIR}" | head
