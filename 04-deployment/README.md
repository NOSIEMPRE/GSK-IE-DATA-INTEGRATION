# 04 — Deployment

Deployment scripts and configurations for the RWD TrustChain pipeline.

## Governance Dashboard

Streamlit app for data quality, HBV cascade, and provenance visualization.

**URL:** http://localhost:8501

**Run** (from project root):

```bash
streamlit run 04-deployment/app.py
```

**Features:**

- **HBV-Style Care Cascade** — Testing → Diagnosis → Treatment funnel (Synthea proxy)
- **Data Quality & AI Validation** — Checks passed/failed, anomaly detection (IF or Ensemble)
- **Provenance & Hash Anchoring** — Manifest ID, anchored assets
- **MLflow Link** — Sidebar link to http://localhost:5000 (experiment `rwd-trustchain-quality`)

## Purpose

- API / dashboard deployment (e.g., Render, AWS)
- Docker / container configs
- Environment setup

