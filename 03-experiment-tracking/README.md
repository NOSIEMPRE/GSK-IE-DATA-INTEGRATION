# 03 — Experiment Tracking

ML experiment tracking, provenance, and hash anchoring for the RWD TrustChain.

## Scripts

| Script | Purpose |
|--------|---------|
| `anchor_hashes.py` | Compute SHA256 hashes of OMOP snapshot, quality reports, ETL specs; output provenance manifest |

## Purpose

- Hash anchoring for audit trail (simulates blockchain provenance)
- Model parameters and metrics (e.g., MLflow, DVC)
- Validation run artifacts
- Reproducibility configs
