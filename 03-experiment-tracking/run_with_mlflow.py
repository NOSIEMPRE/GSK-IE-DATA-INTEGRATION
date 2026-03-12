"""
RWD TrustChain — MLflow experiment tracking.

Runs validation + hash anchoring, logs metrics and artifacts to MLflow.
Each run is tracked as an experiment for reproducibility and comparison.

Usage (from project root):
    python 03-experiment-tracking/run_with_mlflow.py
    python 03-experiment-tracking/run_with_mlflow.py --scenario scenario2

Prerequisites:
    - DuckDB at data/synthea1k.duckdb
    - pip install mlflow
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import mlflow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MLRUNS_DIR = PROJECT_ROOT / "mlruns"
QUALITY_DIR = PROJECT_ROOT / "data" / "quality_reports"
PROVENANCE_DIR = PROJECT_ROOT / "data" / "provenance"

MLFLOW_EXPERIMENT = "rwd-trustchain-quality"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["scenario1", "scenario2"], default="scenario1")
    args = parser.parse_args()

    # Use absolute path so MLflow always writes to project mlruns (regardless of cwd)
    mlflow.set_tracking_uri(MLRUNS_DIR.resolve().as_uri())
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    run_name = f"validation_{args.scenario}"
    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("scenario", args.scenario)

        # 1. Run validation
        subprocess.run(
            [sys.executable, "02-data-sampling-feature/validate_omop_quality.py", "--scenario", args.scenario],
            check=True,
            cwd=PROJECT_ROOT,
        )

        # 2. Load latest quality report
        reports = sorted(QUALITY_DIR.glob("quality_report_*.json"), reverse=True)
        if not reports:
            raise SystemExit("No quality report found")

        with open(reports[0], "r", encoding="utf-8") as f:
            report = json.load(f)

        # 3. Log metrics
        summary = report.get("summary", {})
        mlflow.log_metric("checks_passed", summary.get("passed", 0))
        mlflow.log_metric("checks_warnings", summary.get("warnings", 0))
        mlflow.log_metric("checks_failed", summary.get("failed", 0))

        ai = report.get("ai_validation", {})
        if ai.get("status") == "completed":
            mlflow.log_metric("ai_anomaly_count", ai.get("anomaly_count", 0))
            mlflow.log_metric("ai_total_analyzed", ai.get("total_analyzed", 0))
            mlflow.log_param("ai_target", ai.get("target", ""))

        # 4. Log quality report as artifact
        mlflow.log_artifact(str(reports[0]), artifact_path="quality_reports")

        # 5. Run hash anchoring
        subprocess.run(
            [sys.executable, "03-experiment-tracking/anchor_hashes.py"],
            check=True,
            cwd=PROJECT_ROOT,
        )

        # 6. Log latest provenance manifest
        manifests = sorted(PROVENANCE_DIR.glob("provenance_manifest_*.json"), reverse=True)
        if manifests:
            mlflow.log_artifact(str(manifests[0]), artifact_path="provenance")

        mlflow.log_param("pipeline", "validate+anchor")

    print(f"Logged to MLflow experiment: {MLFLOW_EXPERIMENT} (scenario={args.scenario})")
    print(f"Tracking store: {MLRUNS_DIR}")
    print("View with: bash 03-experiment-tracking/mlflow_ui.sh  →  http://localhost:5000")


if __name__ == "__main__":
    main()
