# 02 — Data Sampling & Feature Engineering

Data sampling strategies, validation, and PPRL for HBV RWD.

## Scripts

| Script | Purpose |
|--------|---------|
| `validate_omop_quality.py` | Rule-based checks + AI anomaly detection; output JSON report |
| `pprl_multi_source_demo.py` | PPRL demo: simulates EHR + Lab sources, deterministic hash linkage |

**Validation scenarios**: `--scenario scenario1` (Isolation Forest) or `--scenario scenario2` (IF+LOF+OCSVM ensemble).

**PPRL**: Simulates two sources from Synthea, outputs `data/pprl/linkage_map_*.json`. Run via `bash run_demo.sh --pprl`.

Requires DuckDB database from `01-initial-notebook/load_synthea_duckdb.py`.

## Purpose

- Sampling logic for OMOP datasets
- Feature extraction for AI validation
- PPRL linkage preparation
