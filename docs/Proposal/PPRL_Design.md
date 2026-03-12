# PPRL Design — Privacy-Preserving Record Linkage for RWD TrustChain

> Design document for cross-source patient-level linkage in HBV real-world data, aligned with GSK IE Challenge requirements and GDPR/EU AI Act compliance.

---

## 1. Problem Statement

### 1.1 Challenge Context

HBV real-world data is **fragmented** across multiple sources:

| Source | Typical Content | Identifiers |
|--------|-----------------|-------------|
| **EHR** | Encounters, diagnoses, procedures | Hospital-specific patient IDs |
| **Lab** | HBsAg, HBV DNA, ALT/AST, biomarkers | Lab system IDs |
| **Pharmacy** | Dispensation records, prescriptions | Pharmacy/claims IDs |
| **Claims** | Billing, procedures, medications | Payer-specific member IDs |

**Core problem**: No shared patient identifier across sources. Direct linkage using names, DOB, or SSN would expose PHI and violate GDPR/HIPAA.

### 1.2 GSK Challenge Requirement

> *"Enable privacy-preserving patient-level linkage across data sources"*

The PPRL service must:

1. **Generate privacy-preserving linkage keys** — no plaintext PHI leaves source systems
2. **Produce linkage map**: `(source_id, source_system) → OMOP person_id`
3. **Support longitudinal OMOP** — merged patient timeline for downstream analysis

---

## 2. Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Privacy by design** | PHI never leaves source in identifiable form; only encrypted/pseudonymized tokens are exchanged |
| **Deterministic linkage keys** | Same patient → same key across runs (for reproducibility and audit) |
| **Separation of duties** | Linkage logic isolated from ETL; configurable, auditable |
| **GDPR alignment** | Minimization, pseudonymization, purpose limitation; no PHI on blockchain |

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PPRL Service — Conceptual Flow                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

  Source A (EHR)              Source B (Lab)              Source C (Pharmacy)
  ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
  │ Local IDs    │            │ Local IDs    │            │ Local IDs    │
  │ + Linkage    │            │ + Linkage    │            │ + Linkage    │
  │   Attributes │            │   Attributes │            │   Attributes │
  └──────┬───────┘            └──────┬───────┘            └──────┬───────┘
         │                           │                           │
         │  Encrypt (Bloom/Salt)     │                           │
         ▼                           ▼                           ▼
  ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
  │ Linkage Keys │            │ Linkage Keys │            │ Linkage Keys │
  │ (no PHI)     │            │ (no PHI)     │            │ (no PHI)     │
  └──────┬───────┘            └──────┬───────┘            └──────┬───────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │     PPRL Matching Engine       │
                    │  (probabilistic / Bloom-based) │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │  Linkage Map (audit-only)      │
                    │  source_id → OMOP person_id   │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │  Longitudinal OMOP Dataset     │
                    │  (merged person-level timeline)│
                    └────────────────────────────────┘
```

---

## 4. Linkage Attributes

### 4.1 Standard Blocking & Matching Attributes

| Attribute | Use | Privacy Treatment |
|-----------|-----|-------------------|
| **DOB (year)** | Blocking (reduce comparison space) | Generalized to year or 5-year band |
| **Sex / Gender** | Blocking | Categorical, low re-identification risk |
| **Postcode (first 3 digits)** | Blocking | Geographic band only |
| **Name (soundex/metaphone)** | Matching | Bloom filter encoding |
| **DOB (full)** | Matching | Bloom filter or secure hash with salt |
| **Address components** | Matching | Bloom filter on q-grams |

**OMOP CDM alignment**: `person` table provides `year_of_birth`, `gender_concept_id`; source-specific identifiers stay in `person` extensions or a separate `person_source` mapping table.

### 4.2 What Stays Local

- Raw names, addresses, SSN, full DOB — **never** transmitted
- Only linkage keys (Bloom filters or salted hashes) leave the source

---

## 5. Technical Approaches

### 5.1 Option A: Bloom Filter–Based PPRL (Recommended for Scale)

| Aspect | Design |
|--------|--------|
| **Technique** | Encode linkage attributes into Bloom filters; compare filter similarity (Jaccard, Dice) |
| **Pros** | Proven in healthcare; supports fuzzy matching; no PHI in filters |
| **Cons** | Parameter tuning (k, m); possible false positives |
| **References** | Schnell et al., BMC Med Inform Decis Mak 2009; PMC8318574 |

**Flow**:

1. At each source: extract blocking + matching attributes
2. Encode matching attributes into Bloom filters (q-grams, k hash functions)
3. Send filters + blocking keys to linkage engine (no PHI)
4. Engine: block by (year_of_birth, gender, region), then match within blocks by filter similarity
5. Output: linkage map `(source_system, source_person_id) → person_id`

### 5.2 Option B: Cryptographic Hashing (Deterministic, Simple)

| Aspect | Design |
|--------|--------|
| **Technique** | SHA256(name + DOB + salt) per source; same patient → same hash if attributes match |
| **Pros** | Simple, deterministic, no third-party matching engine |
| **Cons** | No fuzzy matching; minor data entry errors break linkage |
| **Use case** | Clean, standardized synthetic data (e.g., Synthea) |

### 5.3 Option C: Secure Multi-Party Computation (SMPC)

| Aspect | Design |
|--------|--------|
| **Technique** | Two or more parties compute linkage without revealing plaintext |
| **Pros** | Strong privacy; no trusted linkage center |
| **Cons** | Complex; higher compute cost; requires specialized infrastructure |
| **Use case** | Cross-region EHR federation (e.g., EHDS) |

---

## 6. Outputs & Integration with OMOP

### 6.1 Linkage Map Schema

```json
{
  "linkage_run_id": "20260312_001",
  "created_at": "2026-03-12T12:00:00Z",
  "sources": ["EHR", "Lab", "Pharmacy"],
  "mappings": [
    {"source_system": "EHR", "source_person_id": "E001", "person_id": 1},
    {"source_system": "Lab", "source_person_id": "L042", "person_id": 1},
    {"source_system": "Pharmacy", "source_person_id": "P089", "person_id": 1}
  ],
  "metrics": {
    "total_source_records": 5000,
    "unique_persons_linked": 1200,
    "match_rate": 0.96
  }
}
```

### 6.2 OMOP Integration

- **`person` table**: One row per `person_id`; linkage map provides `person_id` for each source record
- **`person_source` (optional)**: Extended table storing `(person_id, source_system, source_person_id)` for audit
- **Longitudinal OMOP**: ETL merges records from all sources by `person_id` into `condition_occurrence`, `drug_exposure`, `measurement`, etc.

### 6.3 Provenance & Hash Anchoring

- **PPRL config**: Salt, Bloom parameters, blocking rules — hashed and anchored
- **Linkage map**: Stored in secure, access-controlled location; hash anchored (not full map on blockchain)
- **Audit trail**: Who ran linkage, when, which config — in provenance manifest

---

## 7. Compliance Mapping

For full GDPR, EU AI Act, HIPAA, and 21 CFR Part 11 mapping, see [Production_Readiness_and_Compliance.md](Production_Readiness_and_Compliance.md).

| Requirement | PPRL Design Response |
|--------------|----------------------|
| **GDPR Art. 5 (minimization)** | Only linkage attributes used; no unnecessary PHI |
| **GDPR Art. 32 (security)** | Pseudonymization; Bloom filters / hashes non-reversible |
| **GDPR Art. 25 (privacy by design)** | PHI never leaves source in identifiable form |
| **HIPAA** | No PHI in linkage keys; BAA-compliant linkage service |
| **21 CFR Part 11** | Linkage config, run ID, timestamp in provenance |
| **NO PHI on blockchain** | Only hashes of config and linkage map metadata anchored |

---

## 8. Implementation Roadmap

### 8.1 Current Pilot (Single Source)

| Status | Note |
|--------|------|
| **Synthea OMOP 1k** | Single source; no cross-source linkage needed |
| **PPRL** | Design reserved; this document defines the approach |

### 8.2 Phase 2: Multi-Source Demo

| Step | Deliverable |
|------|-------------|
| 1 | Add second source (e.g., CMS DE-SynPUF or synthetic Lab) |
| 2 | Implement Option B (deterministic hash) for PoC |
| 3 | Produce linkage map; merge into longitudinal OMOP |
| 4 | Hash anchor PPRL config and linkage map metadata |

### 8.3 Phase 3: Production-Ready PPRL

| Step | Deliverable |
|------|-------------|
| 1 | Bloom filter–based PPRL (Option A) |
| 2 | Independent linkage service (Lambda / ECS) |
| 3 | Configurable blocking and matching rules |
| 4 | Full audit trail for provenance |

---

## 9. References

- Schnell, R., Bachteler, T., & Reiher, J. (2009). Privacy-preserving record linkage using Bloom filters. *BMC Medical Informatics and Decision Making*, 9(1), 41.
- Vatsalan, D., et al. (2017). Privacy-preserving record linkage for big data: Current approaches and research challenges. *Handbook of Big Data Technologies*.
- GSK IE Challenge — Data Objective (2026). Privacy-preserving linkage, OMOP CDM, blockchain anchoring.

---

*Document version: 1.0 | Date: 2026-03-12*
