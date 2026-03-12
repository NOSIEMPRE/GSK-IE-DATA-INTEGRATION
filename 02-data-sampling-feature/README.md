# 02 — Data Sampling & Feature Engineering

Data sampling strategies and feature engineering for HBV RWD.

## Scripts

| Script | Purpose |
|--------|---------|
| `validate_omop_quality.py` | Rule-based checks + AI anomaly detection (Isolation Forest); output JSON report |

Requires DuckDB database from `01-initial-notebook/load_synthea_duckdb.py`.

## Purpose

- Sampling logic for OMOP datasets
- Feature extraction for AI validation
- PPRL linkage preparation
