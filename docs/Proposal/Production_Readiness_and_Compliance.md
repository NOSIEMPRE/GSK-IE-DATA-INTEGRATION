# RWD TrustChain — Production Readiness & Compliance

> This document describes how the local Pilot maps to production architecture and how it addresses healthcare compliance requirements (GDPR, EU AI Act, HIPAA, 21 CFR Part 11).

---

## 1. Local Components → Production Mapping

| Concept | Local Pilot | Production Alternative | Scalability Notes |
|---------|-------------|------------------------|-------------------|
| **Secure Landing** | `data/synthea1k/` directory | Amazon S3 + SSE-KMS + IAM | S3 supports PB-scale storage, multi-region replication; IAM fine-grained access control |
| **ETL & OMOP** | `load_synthea_duckdb.py` + DuckDB | AWS Glue + RDS PostgreSQL | Glue serverless, on-demand scaling; RDS read replicas, multi-AZ |
| **Storage** | DuckDB single file | RDS PostgreSQL / Aurora | Same OMOP schema; change connection string on migration |
| **PPRL** | Single source (design only); see `PPRL_Design.md` | Standalone PPRL Service (Lambda / ECS) | Cryptographic hashing, pseudonymization, Bloom filter, SMPC pluggable |
| **AI Validation** | `validate_omop_quality.py` (scenario1/scenario2) | SageMaker / Lambda + ML models | Rules + IF/Ensemble coexist; SageMaker for training and inference |
| **Hash Anchoring** | `anchor_hashes.py` → JSON | Same logic → Permissioned Blockchain | Hash algorithm and attestation logic unchanged; output target switches to chain |
| **Governance Dashboard** | Streamlit (`04-deployment/app.py`) | QuickSight / custom React + API | HBV cascade, quality, provenance, MLflow link; frontend replaceable |

---

## 2. Data Volume Scaling Path

| Data Scale | Local Pilot | Production Recommendation |
|------------|-------------|---------------------------|
| **1k–10k persons** | DuckDB single-node | Same, or RDS single instance |
| **10k–100k persons** | DuckDB still viable | RDS larger instance; Glue batch ETL |
| **100k–1M+ persons** | Requires batching/partitioning | RDS read replicas; Glue parallel jobs; S3 partitioned storage |
| **Multi-region / federated** | N/A | EHDS federated architecture; cross-region PPRL |

**Conclusion**: TrustChain flow and schema are data-volume agnostic; scaling mainly adjusts storage and compute resources without changing core logic.

---

## 3. Compliance Mapping

### 3.1 GDPR — Article-Level Mapping

| GDPR Article | Requirement | TrustChain Implementation | Evidence |
|--------------|-------------|---------------------------|----------|
| **Art. 5(1)(c) Data minimization** | Process only data necessary for the purpose | OMOP CDM stores only clinical/operational fields; PPRL uses linkage attributes only (YOB, gender); no raw names/addresses in linkage keys | `PPRL_Design.md` §4; `validate_omop_quality.py` |
| **Art. 5(1)(f) Integrity & confidentiality** | Appropriate security of personal data | Hash anchoring; no PHI on blockchain; provenance manifest for audit | `anchor_hashes.py`; §3.2 |
| **Art. 25 Data protection by design and by default** | Technical and organizational measures; pseudonymization | PPRL design: linkage keys only, no PHI transmitted; default processing limited to necessary scope | `PPRL_Design.md` §2, §4 |
| **Art. 32 Security of processing** | Encryption, pseudonymization, resilience, regular testing | Production: S3 SSE-KMS, IAM; PPRL: salted hashes, non-reversible linkage keys | `PPRL_Design.md` §5; production mapping |
| **Art. 33 Breach notification** | Notify supervisory authority within 72h | Production process; not applicable to synthetic Pilot | N/A (synthetic data) |
| **Art. 35 DPIA** | Data protection impact assessment for high-risk processing | Required for production with real PHI; Pilot uses Synthea (synthetic) | Roadmap item |

### 3.2 EU AI Act — High-Risk AI Governance

| EU AI Act Requirement | TrustChain Implementation | Evidence |
|-----------------------|---------------------------|----------|
| **Risk management** | AI validation (anomaly detection) operates on OMOP; rules + ML; configurable contamination/threshold | `validate_omop_quality.py`; scenario1/scenario2 |
| **Data governance** | OMOP CDM standard; quality reports; provenance manifest | `data/quality_reports/`; `anchor_hashes.py` |
| **Technical documentation** | Validation logic documented; MLflow logs model params and metrics | `02-data-sampling-feature/README.md`; MLflow artifacts |
| **Transparency** | Dashboard shows AI validation status, anomaly counts, module used | `04-deployment/app.py` |
| **Human oversight** | Validation outputs require human review before downstream use; no autonomous decision on patient care | Design principle |
| **Record-keeping** | Provenance manifest; quality reports; MLflow runs | `data/provenance/`; `data/quality_reports/`; `mlruns/` |
| **Accuracy & robustness** | Isolation Forest + ensemble (scenario2); configurable; no direct clinical decision | `validate_omop_quality.py` |

**Note**: The Pilot’s AI validation (anomaly detection on data quality) may fall below “high-risk” under Annex III; production deployment with real PHI would require formal classification and conformity assessment.

### 3.3 HIPAA (US)

| HIPAA Requirement | TrustChain Implementation | Evidence |
|-------------------|---------------------------|----------|
| **Administrative safeguards** | Access control, training (production); Pilot: local only | Production roadmap |
| **Physical safeguards** | Production: S3, RDS in compliant regions; Pilot: local filesystem | Production mapping |
| **Technical safeguards** | Encryption at rest (S3 SSE-KMS); encryption in transit (TLS); no PHI on blockchain | `anchor_hashes.py`; PPRL design |
| **Audit controls** | Provenance manifest; hash anchoring; linkage map metadata | `data/provenance/`; `data/pprl/` |
| **Minimum necessary** | OMOP + PPRL use only necessary attributes; no raw PHI in linkage | `PPRL_Design.md` |

### 3.4 21 CFR Part 11 (FDA Electronic Records)

| 21 CFR Part 11 Requirement | TrustChain Implementation | Evidence |
|---------------------------|---------------------------|----------|
| **Electronic records integrity** | Hash anchoring of OMOP snapshot, ETL specs, validation scripts, quality reports | `anchor_hashes.py` |
| **Audit trail** | Provenance manifest with timestamp, asset hashes, run ID | `data/provenance/provenance_manifest_*.json` |
| **Validation** | Validation scripts versioned; quality reports record checks and AI results | `validate_omop_quality.py`; `data/quality_reports/` |
| **Access controls** | Production: IAM/RBAC; Pilot: filesystem permissions | Production roadmap |

### 3.5 NO PHI on Blockchain

| Principle | Implementation | Evidence |
|------------|----------------|----------|
| **Hash only** | `anchor_hashes.py` outputs only `hash_value` (SHA256); no PHI in manifest | `anchor_hashes.py` |
| **Linkage map** | PPRL linkage map stored in access-controlled location; only hash anchored, not full map on chain | `PPRL_Design.md` §6.3 |
| **Provenance metadata** | Manifest contains asset paths, hashes, timestamps; no patient identifiers | `data/provenance/` |

---

## 4. Compliance Checklist (Pre-Production)

- [ ] Data encryption (TLS in transit, KMS at rest)
- [ ] Access control (IAM / RBAC, least privilege)
- [ ] Audit logging (who accessed/modified what, when)
- [ ] Data retention and deletion policy (GDPR right to erasure)
- [ ] AI model governance (EU AI Act: data, monitoring, documentation)
- [ ] No PHI on blockchain (hashes/metadata only)
- [ ] DPIA for production with real PHI
- [ ] BAA with cloud provider (HIPAA)

---

## 5. AI Module Extensibility

| Current Implementation | Production Extension |
|------------------------|----------------------|
| Rule engine (null, time logic, foreign key) | Retain as first line of defense |
| scenario1: Isolation Forest; scenario2: IF+LOF+OCSVM ensemble | Replaceable with SageMaker custom models, LLM validation |
| Future: Gap prediction model | XGBoost / neural network, hosted on SageMaker |

**Design principle**: AI modules are decoupled from data and storage layers; inputs/outputs are structured JSON for easy replacement and versioning.

---

## 6. Migration to Production

1. **Schema unchanged**: OMOP CDM is standardized; DuckDB → PostgreSQL requires `pgloader` or ETL script only.
2. **Containerize scripts**: Package `load_*`, `validate_*`, `anchor_*` as Docker images; run on ECS / Lambda.
3. **Externalize config**: Database connection, S3 paths, blockchain endpoint from environment variables / Secrets Manager.
4. **Hash output to chain**: `anchor_hashes.py` logic unchanged; submit manifest to Hyperledger Fabric or other permissioned chain API.

---

*Document version: 1.0 | Date: 2026-03-12*
