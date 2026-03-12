# 01 — Initial Notebook

Data setup and initial exploratory data analysis (EDA) for RWD/OMOP pipeline.

## Scripts (run in order)

| Script | Purpose |
|--------|---------|
| `download_synthea_omop.sh` | Download Synthea OMOP 1k from AWS S3 |
| `load_synthea_duckdb.py` | Load OMOP CSVs into DuckDB |
| `synthea_omop_exploration.ipynb` | Explore data, run treatment-gap analysis |

## Purpose

- Raw data exploration
- OMOP mapping validation
- Early pipeline prototyping

