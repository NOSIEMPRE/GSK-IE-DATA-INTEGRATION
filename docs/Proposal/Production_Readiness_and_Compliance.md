# RWD TrustChain — Production Readiness & Compliance

> 本文档说明本地 Pilot 如何映射到生产级架构，以及如何满足医疗行业的高合规要求。

---

## 一、本地组件 → 生产组件映射

| 概念层 | 本地 Pilot | 生产级替代 | 扩展性说明 |
|--------|------------|------------|------------|
| **Secure Landing** | `data/synthea1k/` 目录 | Amazon S3 + SSE-KMS + IAM | S3 支持 PB 级存储、多区域复制；IAM 细粒度访问控制 |
| **ETL & OMOP** | `load_synthea_duckdb.py` + DuckDB | AWS Glue + RDS PostgreSQL | Glue 无服务器、按需扩展；RDS 支持读写分离、多 AZ |
| **存储** | DuckDB 单文件 | RDS PostgreSQL / Aurora | 同一 OMOP schema，迁移时仅改连接串 |
| **PPRL** | 单源（暂无） | 独立 PPRL Service（Lambda / ECS） | 加密哈希、假名化、安全多方计算可插拔 |
| **AI Validation** | `validate_omop_quality.py` + Isolation Forest | SageMaker / Lambda + ML 模型 | 规则 + ML 可并存；SageMaker 支持训练与推理托管 |
| **Hash Anchoring** | `anchor_hashes.py` → JSON | 同上逻辑 → Permissioned Blockchain | 哈希算法与存证逻辑不变，仅输出目标改为链上 |
| **Governance Dashboard** | Streamlit（待实现） | QuickSight / 自建 React + API | 数据源与 API 一致，前端可替换 |

---

## 二、数据量扩展路径

| 数据规模 | 本地 Pilot | 生产建议 |
|----------|------------|----------|
| **1k–10k 人** | DuckDB 单机 | 同左，或 RDS 单实例 |
| **10k–100k 人** | DuckDB 仍可 | RDS 增大实例；Glue 分批 ETL |
| **100k–1M+ 人** | 需分批/分区 | RDS 读写分离；Glue 并行 job；S3 分区存储 |
| **多区域/联邦** | 不适用 | EHDS 联邦架构；跨区域 PPRL |

**结论**：TrustChain 的流程与 schema 与数据量无关；扩展时主要调整存储与计算资源，不改变核心逻辑。

---

## 三、合规性设计

### 3.1 已内置的合规原则

| 合规项 | 设计体现 | 本地实现 | 生产实现 |
|--------|----------|----------|----------|
| **NO PHI on Blockchain** | 仅哈希上链 | `anchor_hashes.py` 只输出 hash_value | 同上，提交到 permissioned chain |
| **GDPR** | 最小必要、假名化、访问控制 | 数据本地、无 PHI 上链 | S3 加密、IAM、假名化 pipeline |
| **HIPAA** | 加密、审计、访问日志 | 本地文件权限 | S3 SSE-KMS、CloudTrail、IAM |
| **21 CFR Part 11** | 电子记录可审计 | Provenance manifest 记录每步 | 同上 + 链上不可篡改 |
| **EU AI Act** | 高风险 AI 治理 | AI 模块可独立审计 | 模型注册、监控、可解释性 |

### 3.2 合规检查清单（生产部署前）

- [ ] 数据加密（传输 TLS，静态 KMS）
- [ ] 访问控制（IAM / RBAC，最小权限）
- [ ] 审计日志（谁在何时访问/修改了何数据）
- [ ] 数据保留与删除策略（GDPR 被遗忘权）
- [ ] AI 模型治理（EU AI Act：数据、监控、文档）
- [ ] 无 PHI 上链（仅哈希/元数据）

---

## 四、AI 模块的可扩展性

| 当前实现 | 生产扩展 |
|----------|----------|
| 规则引擎（null、时间、外键） | 保留，作为第一道防线 |
| Isolation Forest（measurement 异常值） | 可替换为 SageMaker 自定义模型、LLM 校验 |
| 未来：Gap 预测模型 | XGBoost / 神经网络，托管于 SageMaker |

**设计原则**：AI 模块与数据层、存储层解耦；输入输出为结构化 JSON，便于替换与版本管理。

---

## 五、迁移到生产的步骤建议

1. **Schema 不变**：OMOP CDM 已标准化，DuckDB → PostgreSQL 仅需 `pgloader` 或 ETL 脚本。
2. **脚本容器化**：将 `load_*`、`validate_*`、`anchor_*` 打包为 Docker 镜像，在 ECS / Lambda 中运行。
3. **配置外置**：数据库连接、S3 路径、区块链端点等从环境变量/Secrets Manager 读取。
4. **Hash 输出改链**：`anchor_hashes.py` 的逻辑不变，将 manifest 提交到 Hyperledger Fabric / 其他 permissioned chain 的 API。

---

*文档版本：初稿 | 日期：2026-03-12*
