# 03 — Experiment Tracking

ML experiment tracking, provenance, and hash anchoring for the RWD TrustChain.

**MLflow UI:** [http://localhost:5000](http://localhost:5000) | Experiment: `rwd-trustchain-quality`

## Scripts & Notebooks


| Item                 | Purpose                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| `anchor_hashes.py`   | Compute SHA256 hashes of OMOP snapshot, quality reports, ETL specs; output provenance manifest |
| `run_with_mlflow.py` | Run validation + hash anchoring and log metrics/artifacts to MLflow                            |
| `scenario-1.ipynb`   | Baseline: rules + Isolation Forest (single field)                                              |
| `scenario-2.ipynb`   | AI-enhanced: rules + multi-field + ensemble (IF+LOF+OCSVM) voting                              |
| `mlflow_ui.sh`       | Launch MLflow UI from project root                                                             |


## Scenarios


| Scenario       | AI Anomaly Detection            | Description                                                              |
| -------------- | ------------------------------- | ------------------------------------------------------------------------ |
| **Scenario 1** | Isolation Forest                | Single field (`drug_exposure.quantity` or `measurement.value_as_number`) |
| **Scenario 2** | IF + LOF + One-Class SVM voting | Multi-field; anomaly if ≥2 algorithms agree                              |


## MLflow Experiment Tracking

Each run logs:

- **Metrics**: `checks_passed`, `checks_warnings`, `checks_failed`, `ai_anomaly_count`, `ai_total_analyzed`
- **Params**: `scenario`, `ai_target`, `pipeline`
- **Artifacts**: quality report JSON, provenance manifest JSON

**Usage** (from project root):

```bash
# One command: logs scenario1 + scenario2, auto-starts MLflow UI in background
bash run_demo.sh --mlflow

# Or run individually (no UI auto-start):
python 03-experiment-tracking/run_with_mlflow.py --scenario scenario1
python 03-experiment-tracking/run_with_mlflow.py --scenario scenario2
bash 03-experiment-tracking/mlflow_ui.sh
```

**View runs** — MLflow UI: **[http://localhost:5000](http://localhost:5000)**

> ⚠️ Use `bash 03-experiment-tracking/mlflow_ui.sh` so MLflow reads from project `mlruns/`. The Governance Dashboard sidebar link deep-links to `rwd-trustchain-quality` when the experiment exists.

## Purpose

- Hash anchoring for audit trail (simulates blockchain provenance)
- MLflow experiment tracking for validation metrics and artifacts
- Reproducibility configs

