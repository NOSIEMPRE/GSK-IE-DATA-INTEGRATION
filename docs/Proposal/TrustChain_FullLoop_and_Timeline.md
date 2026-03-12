# RWD TrustChain — Full Loop & Timeline

> 本文档说明 TrustChain 端到端流程、与 AWS 架构的对应关系，以及项目时间线与里程碑。

---

## 一、架构文档 vs 实际实现

| 维度 | AWS 架构文档 (RWD TrustChain Tech Architecture.png) | 本 Pilot 实现 |
|------|------------------------------------------------------|---------------|
| **定位** | 生产级参考架构（云原生、可扩展） | 本地 Demo / PoC（验证概念、可复现） |
| **数据源** | EHR、Lab、Pharmacy、Claims 多源 | Synthea OMOP 单源（模拟多源） |
| **Secure Landing** | S3 + SSE-KMS + IAM | 本地 `data/synthea1k/` |
| **ETL & OMOP** | AWS Glue + RDS PostgreSQL | `load_synthea_duckdb.py` + DuckDB |
| **PPRL** | 独立 PPRL Service | 设计预留（单源暂无） |
| **AI Validation** | SageMaker | `validate_omop_quality.py`（规则引擎） |
| **Hash Anchoring** | SageMaker → Blockchain | `anchor_hashes.py` → JSON manifest |
| **Governance Dashboard** | 独立 Dashboard | 待实现（Streamlit） |

**结论**：架构文档描述的是 **AWS 生产蓝图**；本 Pilot 用 **本地/轻量工具** 实现 **同一概念流程**，便于快速验证和演示。

---

## 二、TrustChain Full Loop（端到端流程）

### 2.1 概念层（与架构图一致）

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

### 2.2 本 Pilot 实现层（Step-by-Step）

| Step | 概念环节 | 本 Pilot 实现 | 产出物 |
|------|----------|---------------|--------|
| **1** | Ingest | `download_synthea_omop.sh` | `data/synthea1k/*.csv` |
| **2** | Standardize | `load_synthea_duckdb.py` | `data/synthea1k.duckdb` |
| **3** | Validate | `validate_omop_quality.py` | `data/quality_reports/quality_report_*.json` |
| **4** | Anchor | `anchor_hashes.py` | `data/provenance/provenance_manifest_*.json` |
| **5** | Govern | Streamlit Dashboard（待实现） | 可视化界面 |

### 2.3 数据流与信任链

```
Synthea OMOP (AWS S3)
        │
        ▼
  data/synthea1k/*.csv  ──────────────────────────────────────────────────────────
        │                                                                          │
        ▼                                                                          │
  synthea1k.duckdb  ──► validate_omop_quality.py  ──► quality_report_*.json         │
        │                          │                            │                  │
        │                          │                            │                  │
        └──────────────────────────┴────────────────────────────┴──────────────────┘
                                        │
                                        ▼
                              anchor_hashes.py
                                        │
                                        ▼
                              provenance_manifest_*.json
                                        │
                                        ▼
                              Governance Dashboard (Provenance Audit Trail)
```

---

## 三、Timeline & Milestone

### 3.1 总体时间线

```
Week 1–2           Week 3              Week 4              Week 5+
─────────────────────────────────────────────────────────────────────────────►
│ Data + EDA      │ Validation +      │ Hash Anchor +     │ Dashboard +
│ + Quality       │ Refinement        │ Pipeline          │ Deploy + Doc
└────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘
   M1 完成           M2 完成             M3 完成              M4 完成
```

### 3.2 里程碑明细

| 里程碑 | 内容 | 状态 | 交付物 |
|--------|------|------|--------|
| **M1: Data & EDA** | 数据获取、加载、探索 | ✅ Done | `01-initial-notebook/` 全套 |
| **M2: Quality Validation** | 质量规则、完整性、时间逻辑 | ✅ Done | `validate_omop_quality.py` + JSON |
| **M3: Hash Anchoring** | 哈希锚定、Provenance manifest | ✅ Done | `anchor_hashes.py` + manifest |
| **M4: Governance Dashboard** | Streamlit 可视化 | 🔲 Pending | `04-deployment/dashboard.py` |
| **M5: End-to-End Pipeline** | 一键运行脚本 | 🔲 Pending | `run_demo.sh` 或 `Makefile` |
| **M6: PPRL Design** | 隐私保护链接设计文档 | 🔲 Pending | `docs/PPRL_Design.md` |
| **M7: Deploy** | 部署到 Render / 云 | 🔲 Pending | 可访问 URL |
| **M8: Proposal Final** | 提案定稿、架构对齐 | 🔲 Pending | 更新 `docs/Proposal/` |

### 3.3 建议执行顺序

```
当前进度: M1 ✅  M2 ✅  M3 ✅

下一步:
  1. M4 — Governance Dashboard（Streamlit）
  2. M5 — run_demo.sh 串联全流程
  3. M6 — PPRL 设计文档（可并行）
  4. M7 — 部署
  5. M8 — 提案定稿
```

---

## 四、Demo 交付清单

| 类别 | 交付物 | 说明 |
|------|--------|------|
| **可运行** | `run_demo.sh` | 一条命令跑完 01→02→03 |
| **可展示** | Streamlit Dashboard | 质量指标、Provenance 链、Gap 统计 |
| **可审计** | `data/provenance/*.json` | 哈希 manifest，可验证完整性 |
| **可复现** | README + requirements.txt | 环境与步骤说明 |
| **可扩展** | 架构文档 + PPRL 设计 | 与 AWS 生产架构对齐的路线图 |

---

*文档生成日期：2026-03-12*
