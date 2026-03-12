# RWD TrustChain — Full Loop & Timeline

> End-to-end TrustChain flow, mapping to AWS architecture, and project timeline with milestones.

---

## 1. Architecture vs Implementation

| Dimension | AWS Architecture (RWD TrustChain Tech Architecture.png) | Pilot Implementation |
|-----------|----------------------------------------------------------|----------------------|
| **Scope** | Production reference (cloud-native, scalable) | Local Demo / PoC (concept validation, reproducible) |
| **Data sources** | EHR, Lab, Pharmacy, Claims (multi-source) | Synthea OMOP single source (simulates multi-source) |
| **Secure Landing** | S3 + SSE-KMS + IAM | Local `data/synthea1k/` |
| **ETL & OMOP** | AWS Glue + RDS PostgreSQL | `load_synthea_duckdb.py` + DuckDB |
| **PPRL** | Standalone PPRL Service | Design: `PPRL_Design.md`; Demo: `pprl_multi_source_demo.py` (`--pprl`) |
| **AI Validation** | SageMaker | `validate_omop_quality.py` (rules + scenario1/scenario2 anomaly detection) |
| **Hash Anchoring** | SageMaker → Blockchain | `anchor_hashes.py` → JSON manifest |
| **Governance Dashboard** | Standalone Dashboard | `04-deployment/app.py` (Streamlit, HBV cascade, MLflow link) — http://localhost:8501 |

**Conclusion**: The architecture describes the **AWS production blueprint**; the Pilot implements the **same conceptual flow** with local/lightweight tools for rapid validation and demo.

---

## 2. TrustChain Full Loop

### 2.1 Conceptual Layer (aligned with architecture diagram)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        RWD TrustChain — Conceptual Full Loop                      │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │ 1. INGEST   │     │ 2. STANDARD  │     │ 3. VALIDATE  │     │ 4. ANCHOR    │
  │ Fragmented  │ ──► │ OMOP CDM    │ ──► │ Quality &    │ ──► │ Hash to      │
  │ RWD         │     │ + PPRL      │     │ Gap Detect   │     │ Provenance   │
  └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
        │                      │                    │                     │
        ▼                      ▼                    ▼                     ▼
  Secure Landing         ETL Pipeline         AI Validation         Blockchain /
  (S3 / local)           (Glue / DuckDB)      (SageMaker / Py)      Manifest
                                                                          │
                                                                          ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ 5. GOVERNANCE DASHBOARD — Quality Metrics | HBV Cascade | Provenance Trail   │
  └──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Pilot Implementation (Step-by-Step)

| Step | Concept | Pilot Implementation | Output |
|------|---------|----------------------|--------|
| **1** | Ingest | `download_synthea_omop.sh` | `data/synthea1k/*.csv` |
| **2** | Standardize | `load_synthea_duckdb.py` | `data/synthea1k.duckdb` |
| **3** | Validate | `validate_omop_quality.py` | `data/quality_reports/quality_report_*.json` |
| **3b** | PPRL (optional) | `pprl_multi_source_demo.py` | `data/pprl/linkage_map_*.json` |
| **4** | Anchor | `anchor_hashes.py` | `data/provenance/provenance_manifest_*.json` |
| **5** | Govern | `04-deployment/app.py` (Streamlit) | HBV cascade, quality metrics, provenance, MLflow link |

### 2.3 Data Flow & Trust Chain

```
Synthea OMOP (AWS S3)
        │
        ▼
  data/synthea1k/*.csv
        │
        ▼
  synthea1k.duckdb  ──► validate_omop_quality.py  ──► quality_report_*.json
        │                          │                          │
        │  (optional --pprl)       │                          │
        ▼                          │                          │
  pprl_multi_source_demo.py  ──► linkage_map_*.json          │
        │                          │                          │
        └──────────────────────────┴──────────────────────────┘
                                        │
                                        ▼
                              anchor_hashes.py
                                        │
                                        ▼
                              provenance_manifest_*.json
                                        │
                                        ▼
                              Governance Dashboard (http://localhost:8501)
```

---

## 3. Timeline & Milestones

### 3.1 Milestone Summary

| Milestone | Content | Status | Deliverable |
|-----------|---------|---------|-------------|
| **M1: Data & EDA** | Data acquisition, load, exploration | ✅ Done | `01-initial-notebook/` |
| **M2: Quality Validation** | Rules, completeness, time logic | ✅ Done | `validate_omop_quality.py` + JSON |
| **M3: Hash Anchoring** | Hash anchoring, provenance manifest | ✅ Done | `anchor_hashes.py` + manifest |
| **M4: Governance Dashboard** | Streamlit (HBV cascade, MLflow link) | ✅ Done | `04-deployment/app.py` |
| **M5: End-to-End Pipeline** | One-click run script | ✅ Done | `run_demo.sh` |
| **M6: PPRL Design** | Privacy-preserving linkage design | ✅ Done | `docs/Proposal/PPRL_Design.md` |
| **M7: Deploy** | Deploy to Render / cloud | 🔲 Pending | Public URL |
| **M8: Proposal Final** | Unify and update `docs/Proposal/` | ✅ Done | This document |

### 3.2 Next Steps

```
Current: M1 ✅ M2 ✅ M3 ✅ M4 ✅ M5 ✅ M6 ✅ M8 ✅

Remaining: M7 — Deploy
```

---

## 4. Demo Deliverables

| Category | Deliverable | Description |
|----------|-------------|-------------|
| **Runnable** | `run_demo.sh` | 01→02→03→04; `--mlflow` logs scenario1+scenario2 and auto-starts MLflow UI; `--pprl` for PPRL |
| **Dashboard** | Streamlit | http://localhost:8501 — HBV cascade, quality, provenance, MLflow link |
| **Auditable** | `data/provenance/*.json` | Hash manifest for integrity verification |
| **Reproducible** | README + requirements.txt | Environment and steps |
| **Extensible** | Architecture + PPRL + Compliance | [PPRL_Design.md](PPRL_Design.md), [Production_Readiness_and_Compliance.md](Production_Readiness_and_Compliance.md) |

---

## 5. Related Documents

| Document | Purpose |
|----------|---------|
| [RWD_TrustChain_Architecture_Explaination.md](RWD_TrustChain_Architecture_Explaination.md) | Architecture overview, blockchain design |
| [PPRL_Design.md](PPRL_Design.md) | Privacy-preserving record linkage design |
| [Production_Readiness_and_Compliance.md](Production_Readiness_and_Compliance.md) | GDPR, EU AI Act, HIPAA, 21 CFR Part 11 mapping |

---

*Document version: 1.0 | Date: 2026-03-12*
