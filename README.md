# GSK Data Integration — RWD TrustChain

Real-world data (RWD) integration pilot for Hepatitis B, aligned with the GSK IE Challenge. Transforms fragmented healthcare data into OMOP CDM with privacy-preserving linkage, AI validation, and blockchain-anchored provenance.

## Project Structure

```
├── README.md
├── .gitignore
├── .flake8
├── requirements.txt
├── render.yaml                 # Deployment config (Render.com)
├── .github/
│   └── workflows/              # CI/CD (GitHub Actions)
│       └── ci.yml
├── 01-initial-notebook/        # Data setup & EDA
│   ├── download_synthea_omop.sh
│   ├── load_synthea_duckdb.py
│   └── synthea_omop_exploration.ipynb
├── 02-data-sampling-feature/   # Sampling & feature engineering
│   └── validate_omop_quality.py
├── 03-experiment-tracking/     # ML experiment tracking & hash anchoring
│   └── anchor_hashes.py
├── 04-deployment/              # Deployment scripts & configs
├── 05-monitoring/              # Pipeline monitoring
├── 06-cicd/                    # CI/CD pipelines
├── data/                       # Raw & processed datasets
│   ├── synthea1k/             # Synthea OMOP 1k cohort (CSV)
│   ├── quality_reports/       # Validation JSON reports
│   └── provenance/           # Hash manifests (audit trail)
├── docs/
│   ├── Proposal/               # Architecture & design
│   │   ├── RWD_TrustChain_Architecture_Explaination.md
│   │   ├── RWD_TrustChain_Architecture_CN.md
│   │   └── RWD TrustChain Tech Achitecture.png
│   └── Challenge/              # Challenge materials
│       ├── GSK - IE Challenge Data Objective.docx.md
│       └── Challenge RWD Integrity 15Feb2026.pdf
└── venv/                       # Python virtual env (gitignored)
```

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd gsk-data-integration

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Data Setup (Synthea OMOP)

The pilot uses [Synthea OMOP](https://registry.opendata.aws/synthea-omop/) synthetic data. To download and load:

```bash
# 1. Download Synthea OMOP 1k cohort (requires AWS CLI)
bash 01-initial-notebook/download_synthea_omop.sh

# 2. Load CSVs into DuckDB for analysis
python 01-initial-notebook/load_synthea_duckdb.py

# 3. Run exploration notebook
jupyter notebook 01-initial-notebook/synthea_omop_exploration.ipynb

# 4. Run data quality validation (outputs JSON report)
python 02-data-sampling-feature/validate_omop_quality.py

# 5. Hash anchoring (provenance manifest for audit trail)
python 03-experiment-tracking/anchor_hashes.py
```

This creates `data/synthea1k/` (CSV), `data/synthea1k.duckdb` (queryable database), `data/quality_reports/` (validation reports), and `data/provenance/` (hash manifests).

## Deployment

The repo is set up for deployment:

- **`render.yaml`** — Render.com blueprint for web services, cron jobs
- **`04-deployment/`** — Deployment scripts, Docker configs, app entry points
- **`05-monitoring/`** — Health checks, data quality metrics, alerting
- **`06-cicd/`** + **`.github/workflows/`** — Automated CI/CD

To deploy: connect the repo to [Render](https://render.com), uncomment and configure services in `render.yaml`, then add your app code in `04-deployment/`.

## Key Documentation

- **[Architecture (EN)](docs/Proposal/RWD_TrustChain_Architecture_Explaination.md)** — RWD TrustChain technical architecture and blockchain design assessment
- **[Architecture (中文)](docs/Proposal/RWD_TrustChain_Architecture_CN.md)** — 技术架构说明与区块链设计评估
- **[Full Loop & Timeline](docs/Proposal/TrustChain_FullLoop_and_Timeline.md)** — 端到端流程、与 AWS 架构对应、时间线与里程碑
- **[Production Readiness & Compliance](docs/Proposal/Production_Readiness_and_Compliance.md)** — 生产映射、扩展路径、合规清单
- **[Challenge Objective](docs/Challenge/GSK%20-%20IE%20Challenge%20Data%20Objective.docx.md)** — GSK IE Challenge objectives and requirements

## Compliance

- GDPR & HIPAA compliant
- EU AI Act ready
- 21 CFR Part 11 audit trail
- NO PHI on blockchain

## License

TBD
