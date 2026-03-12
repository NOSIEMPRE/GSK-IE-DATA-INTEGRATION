# RWD TrustChain Technical Architecture Explanation

> Architecture overview and blockchain design assessment based on `RWD TrustChain Tech Achitecture.png`

---

## 1. Architecture Overview

**RWD TrustChain: AWS OMOP-Centric Architecture** is an end-to-end real-world data (RWD) processing pipeline designed for fragmented Hepatitis B (HBV) healthcare data. The flow starts with multi-source data ingestion, proceeds through secure landing, ETL standardization, AI validation and gap detection, and culminates in a governance dashboard that provides quality metrics and audit trails. The architecture emphasizes **data compliance, privacy protection, and traceability**.

---

## 2. Component-by-Component Breakdown

### 2.1 Data Source Layer: Fragmented RWD (Hepatitis B)

| Data Source | Description |
|-------------|-------------|
| **EHR Systems** | Electronic health records from hospitals/clinics: patient records, encounters, diagnoses |
| **Lab Data** | Laboratory data: HBsAg, HBV DNA, ALT/AST, and other test results and biomarkers |
| **Pharmacy Records** | Pharmacy records: medication history, prescriptions, antiviral dispensing records |
| **Claims Data** | Claims/administrative data: visits, procedures, medications, reimbursement-related data |

**Purpose**: Serves as the starting point of the data pipeline, providing multi-dimensional, dispersed raw patient data for downstream integration and analysis.

---

### 2.2 Data Landing & Standardization Layer

#### 2.2.1 Secure Data Landing

- **Technology**: Amazon S3
- **Capabilities**:
  - ✓ **Raw Data Ingest**: Entry point for raw data ingestion
  - ✓ **SSE-KMS Encryption**: Server-side encryption via AWS KMS for data at rest
  - ✓ **Access Controls**: Strict access control and permission management

**Purpose**: The first secure entry point for raw RWD into the system, ensuring data security and privacy at rest, aligned with HIPAA, GDPR, and similar requirements.

---

#### 2.2.2 ETL & OMOP CDM (Extract, Transform, Load & OMOP Common Data Model)

- **Technology**: AWS Glue (ETL), Amazon RDS PostgreSQL (storage)
- **Capabilities**:
  - **Data Transformation & OMOP Mapping**: Converts source data into OMOP CDM standard structure
  - **Standardized OMOP Dataset**: Outputs standardized OMOP datasets for cross-source interoperability

**Purpose**: Achieves semantic and structural standardization of data, forming the foundation for downstream analysis, linkage, and auditing. OMOP CDM is the common model in the OHDSI ecosystem, enabling global collaboration and evidence generation.

---

#### 2.2.3 PPRL Service (Privacy-Preserving Record Linkage)

- **Capability**: Privacy-Preserving Record Linkage
- **Relationship with ETL**: Bidirectional interaction with ETL & OMOP CDM; linkage can occur during or after standardization

**Purpose**: Links patient records from EHR, Lab, Pharmacy, and Claims across sources without exposing personally identifiable health information (PHI), building longitudinal patient journeys. Typically uses cryptographic hashing, pseudonymization, secure multi-party computation, and similar techniques.

---

### 2.3 Validation, Detection & Governance Layer

#### 2.3.1 AI Validation & Hash Anchoring

- **Technology**: AWS SageMaker
- **Hash anchoring targets**:
  - **OMOP Snapshots**: OMOP dataset snapshots
  - **ETL Specs**: ETL process specifications and configurations
  - **AI Reports**: AI analysis reports and quality assessment outputs

**Purpose**: Generates cryptographic hashes (fingerprints) for data assets and anchors them to blockchain or tamper-evident storage. Any modification to the original data changes the hash, enabling **data integrity proof** and **provenance auditing**. This is the core input for the blockchain trust chain.

---

#### 2.3.2 AI Validation & Gap Detection

- **Capabilities**:
  - **Data Quality Validation**: Completeness and consistency checks
  - **HBV Gap Detection**: Hepatitis B care cascade gap detection
    - Testing → Diagnosis → Treatment Gaps

**Purpose**: Uses AI to identify data gaps, anomalies, and clinical logic issues, and specifically quantifies key gaps in the HBV patient journey (e.g., undetected, undiagnosed, untreated) to support public health strategy and guideline development.

---

#### 2.3.3 Governance Dashboard

- **Capabilities**:
  - **Quality Metrics & HBV Cascade Analytics**: Quality metrics and HBV cascade analysis
  - **Testing / Diagnosis / Treatment**: Visualization across the care cascade
  - **Provenance Audit Trail**: End-to-end data provenance and audit trail

**Purpose**: Provides a unified interface to monitor data quality, HBV care cascade, and the full data provenance chain. The Provenance Audit Trail builds on hash anchoring to enable **end-to-end auditability** from raw data to analysis outputs.

---

### 2.4 Compliance Statement (Bottom Bar)

| Compliance Item | Description |
|-----------------|-------------|
| **GDPR & HIPAA Compliant** | Aligned with EU General Data Protection Regulation and US healthcare privacy regulations |
| **EU AI Act Ready** | Meets EU AI Act governance requirements for high-risk AI systems |
| **21 CFR Part 11 Audit Trail** | Meets FDA requirements for electronic records and electronic signatures audit trails |
| **NO PHI on Blockchain** | No personally identifiable health information on blockchain; only hashes and metadata are stored |

---

## 3. Blockchain Design Assessment

### 3.1 Design Pattern: Hash On-Chain, Data Off-Chain

The architecture does not show "blockchain" as a separate module, but the concept is reflected in:

- **AI Validation & Hash Anchoring**: Generates and anchors hashes
- **Governance Dashboard → Provenance Audit Trail**: Hash-based audit trail
- **NO PHI on Blockchain**: Clarifies that blockchain carries only metadata, not PHI

This is a typical **Hash Anchoring** pattern: original data and PHI remain off-chain (S3, RDS, etc.); only data fingerprints (hashes) are written to the blockchain.

---

### 3.2 Rationale Assessment

| Dimension | Assessment | Rationale |
|-----------|------------|-----------|
| **Privacy** | ✅ Sound | PHI is not stored on-chain, avoiding GDPR "right to be forgotten," HIPAA minimum necessary, and similar risks; the tension between blockchain immutability and deletion rights is avoided |
| **Data Integrity** | ✅ Sound | Hashes are cryptographic fingerprints; any tampering changes the hash; on-chain hashes provide tamper-evident integrity proof |
| **Traceability** | ✅ Sound | Anchoring hashes for OMOP snapshots, ETL specs, and AI reports enables a full provenance chain from raw data to analysis outputs |
| **Compliance** | ✅ Sound | Aligns with 21 CFR Part 11 auditability for electronic records, while addressing GDPR, HIPAA, and EU AI Act |
| **Performance & Scalability** | ✅ Sound | Large datasets stay in S3/RDS; blockchain handles only verification and trust, avoiding performance limits from storing large volumes on-chain |

---

### 3.3 Potential Improvements

1. **Blockchain Type**: The diagram does not specify public, consortium, or private chain. Healthcare use cases typically use a **Permissioned Blockchain** for access control and compliance auditing.
2. **Hash Anchoring Frequency**: Clarify when OMOP snapshots, ETL specs, and AI reports are anchored (e.g., after each ETL run, daily/weekly batches).
3. **On-Chain Content**: Beyond hashes, consider storing timestamps, data versions, processor identifiers, and other metadata to enrich audit granularity.

---

## 4. Data Flow & Trust Chain Summary

```
Fragmented RWD (EHR, Lab, Pharmacy, Claims)
        ↓
Secure Data Landing (S3, encryption, access controls)
        ↓
ETL & OMOP CDM ←→ PPRL Service
        ↓
AI Validation & Hash Anchoring (hash generation & anchoring)
        ↓
AI Validation & Gap Detection (quality & gap detection)
        ↓
Governance Dashboard (quality metrics + HBV cascade + Provenance Audit Trail)
```

**Trust chain logic**:  
Raw data → Standardization → Hash anchoring → On-chain attestation → Audit trail.  
The "hash on-chain, data off-chain" design achieves data integrity, traceability, and regulatory-grade auditability while protecting privacy.

---

## 5. Use Case & Data Strategy

This section clarifies the relationship between the reference architecture and the GSK Challenge, and proposes concrete scenarios that satisfy data availability, EU compliance, and generalizability.

### 5.1 Architecture Scope

The RWD TrustChain architecture is **disease-agnostic**. The diagram uses Hepatitis B (HBV) as an illustrative use case, but the components—Secure Landing, OMOP ETL, PPRL, AI Validation, Hash Anchoring, and Governance Dashboard—apply to any longitudinal RWD pipeline. Our pilot implements this architecture for a specific scenario while remaining generalizable to other chronic diseases.

### 5.2 Challenge Alignment

We adopt this architecture as the **reference implementation** for the GSK IE Challenge. The pilot will demonstrate:

- Harmonization of fragmented RWD into OMOP CDM  
- Privacy-preserving record linkage across sources  
- AI-based data validation and gap detection  
- Blockchain-anchored provenance and audit trail  
- EU compliance (GDPR, EU AI Act, EHDS, 21 CFR Part 11)

### 5.3 Proposed Scenarios

#### Scenario 1: Synthetic Pan-EU HBV Cohort (Primary Pilot)

| Criterion | Implementation |
|-----------|----------------|
| **Data availability** | [Synthea OMOP](https://registry.opendata.aws/synthea-omop/) (1k / 100k / 2.8M persons) on AWS S3; free, no account required. Alternatively, generate locally via [Synthea](https://github.com/synthetichealth/synthea) + [ETL-Synthea](https://github.com/OHDSI/ETL-Synthea). |
| **EU compliance** | Fully synthetic data—no real PHI. Architecture designed for GDPR (access control, pseudonymization), EU AI Act (governance for high-risk AI), EHDS (interoperability), and 21 CFR Part 11 (audit trail). |
| **Challenge requirements** | OMOP CDM, PPRL, AI validation, hash anchoring, governance dashboard. HBV-specific logic confined to gap-detection rules and cascade analytics. |
| **Generalizability** | TrustChain is disease-agnostic; only clinical rules and metrics are HBV-specific. Swapping rule sets and definitions extends the pipeline to diabetes, heart failure, oncology, etc. |

**Use case narrative**: A synthetic chronic HBV cohort simulating pan-European EHR + Lab + Pharmacy data. The pilot validates the full pipeline (ingest → OMOP → PPRL → AI validation → hash anchoring → dashboard) and demonstrates Testing → Diagnosis → Treatment cascade analytics.

---

#### Scenario 2: Multi-Source Chronic Liver Disease Registry (Extension)

| Criterion | Implementation |
|-----------|----------------|
| **Data availability** | Synthea OMOP (EHR + Lab) + [CMS DE-SynPUF](https://github.com/OHDSI/ETL-CMS) OMOP (claims-like). Both freely downloadable. |
| **EU compliance** | Same as Scenario 1. Multi-source design reinforces PPRL and provenance requirements. |
| **Challenge requirements** | Demonstrates linkage across EHR, Lab, Pharmacy, and Claims-like sources; longitudinal disease course; AI gap detection for HBV/HCV/NASH. |
| **Generalizability** | Platform for chronic liver disease; HBV is the first pilot, with clear path to HCV, NASH, and other conditions. |

**Use case narrative**: A longitudinal registry combining hospital EHR, lab results, pharmacy dispensation, and claims-like data. PPRL links records across sources without exposing PHI. AI identifies gaps in testing, diagnosis, and treatment across HBV, HCV, and NASH.

---

#### Scenario 3: EU-Style Primary Care Chronic Disease Platform (Roadmap)

| Criterion | Implementation |
|-----------|----------------|
| **Data availability** | Synthea OMOP configured for primary care modules; no real patient data. |
| **EU compliance** | Architecture aligned with EHDS federated interoperability and EU primary care data governance. |
| **Challenge requirements** | Same TrustChain components; focus shifts to multi-morbidity, drug safety, and long-term follow-up. |
| **Generalizability** | Demonstrates TrustChain as a reusable RWE platform for EU primary care registries. |

**Use case narrative**: A platform for chronic disease surveillance and drug safety in primary care. Phase 1 (HBV) and Phase 2 (chronic liver disease) validate the architecture; Phase 3 generalizes to multi-morbidity and policy-ready RWE.

### 5.4 Recommended Phasing

| Phase | Scenario | Deliverable |
|-------|----------|-------------|
| **Phase 1** | Scenario 1 (Synthetic HBV) | End-to-end TrustChain pilot with Synthea OMOP; full pipeline demo. |
| **Phase 2** | Scenario 2 (Chronic liver disease) | Multi-source PPRL; extended gap detection. |
| **Phase 3** | Scenario 3 (Primary care platform) | Generalization roadmap; EU EHDS alignment. |

---

## 6. Conclusion

The blockchain design in the RWD TrustChain architecture follows a **hash anchoring + off-chain data** pattern, which is **sound and well-established** for medical RWD. It leverages blockchain’s immutability and auditability while avoiding the privacy and compliance risks of storing PHI on-chain. This aligns with the GSK Challenge objective of "anchoring dataset fingerprints on a permissioned blockchain."

---

*Document generated: 2026-03-12*
