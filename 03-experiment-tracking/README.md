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
# Scenario 1 (default)
python 03-experiment-tracking/run_with_mlflow.py

# Scenario 2
python 03-experiment-tracking/run_with_mlflow.py --scenario scenario2

# Or via demo with --mlflow
bash run_demo.sh --mlflow --no-ui
```

**View runs** — MLflow UI: **[http://localhost:5000](http://localhost:5000)**

> ⚠️ Must run from project root, otherwise you'll only see empty "Default". Use the script:

```bash
bash 03-experiment-tracking/mlflow_ui.sh
```

Or manually:

```bash
cd /path/to/GSK\ DATA\ INTEGRATION
mlflow ui
```

Then open **[http://localhost:5000](http://localhost:5000)** and select experiment **rwd-trustchain-quality** to compare scenario1/scenario2 runs.

## Purpose

- Hash anchoring for audit trail (simulates blockchain provenance)
- MLflow experiment tracking for validation metrics and artifacts
- Reproducibility configs

