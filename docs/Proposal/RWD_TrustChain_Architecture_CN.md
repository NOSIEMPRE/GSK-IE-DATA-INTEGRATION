# RWD TrustChain 技术架构说明

> 基于 `RWD TrustChain Tech Achitecture.png` 的架构解读与区块链设计评估

---

## 一、架构概览

**RWD TrustChain: AWS OMOP-Centric Architecture** 是一个端到端的真实世界数据（RWD）处理管道，专门针对乙型肝炎（Hepatitis B）的碎片化医疗数据。整体流程从多源数据摄取开始，经安全着陆、ETL 标准化、AI 验证与缺陷检测，最终通过治理仪表盘提供质量指标和审计追踪，强调**数据合规性、隐私保护和可追溯性**。

---

## 二、各环节功能详解

### 1. 数据源层：Fragmented RWD (Hepatitis B)

| 数据源 | 说明 |
|--------|------|
| **EHR Systems** | 电子健康记录系统，医院/诊所的患者病历、就诊记录、诊断信息 |
| **Lab Data** | 实验室数据，如 HBsAg、HBV DNA、ALT/AST 等检测结果和生物标记物 |
| **Pharmacy Records** | 药房记录，用药历史、处方信息、抗病毒药物发放记录 |
| **Claims Data** | 理赔/管理数据，就诊、检查、用药等报销相关数据 |

**作用**：作为数据管道的起点，提供多维度、分散的原始患者数据，是后续整合与分析的输入来源。

---

### 2. 数据着陆与标准化层

#### 2.1 Secure Data Landing（安全数据着陆）

- **技术组件**：Amazon S3
- **核心能力**：
  - ✓ **Raw Data Ingest**：原始数据摄取入口
  - ✓ **SSE-KMS Encryption**：使用 AWS KMS 进行服务器端加密，保护静态数据
  - ✓ **Access Controls**：严格的访问控制与权限管理

**作用**：原始 RWD 进入系统的第一个安全入口，确保数据在存储时的安全性和隐私性，符合 HIPAA、GDPR 等要求。

---

#### 2.2 ETL & OMOP CDM（抽取、转换、加载与 OMOP 通用数据模型）

- **技术组件**：AWS Glue（ETL）、Amazon RDS PostgreSQL（存储）
- **核心能力**：
  - **Data Transformation & OMOP Mapping**：将各源数据转换为 OMOP CDM 标准结构
  - **Standardized OMOP Dataset**：输出标准化的 OMOP 数据集，支持跨源互操作

**作用**：实现数据语义统一和结构标准化，是后续分析、链接和审计的基础。OMOP CDM 是 OHDSI 生态的通用模型，便于全球协作与证据生成。

---

#### 2.3 PPRL Service（隐私保护记录链接服务）

- **核心能力**：Privacy-Preserving Record Linkage
- **与 ETL 关系**：与 ETL & OMOP CDM 有双向交互，可在标准化过程中或之后进行记录链接

**作用**：在不暴露个人身份信息（PHI）的前提下，将来自 EHR、Lab、Pharmacy、Claims 等不同来源的同一患者记录进行安全链接，形成纵向患者轨迹。通常采用加密哈希、假名化、安全多方计算等技术。

---

### 3. 验证、检测与治理层

#### 3.1 AI Validation & Hash Anchoring（AI 验证与哈希锚定）

- **技术组件**：AWS SageMaker
- **哈希锚定对象**：
  - **OMOP Snapshots**：OMOP 数据集快照
  - **ETL Specs**：ETL 过程规范与配置
  - **AI Reports**：AI 分析报告与质量评估结果

**作用**：为各类数据资产生成加密哈希（指纹），并将哈希值锚定到区块链或不可篡改存储中。任何对原始数据的篡改都会导致哈希不匹配，从而实现**数据完整性证明**和**溯源审计**，是区块链信任链的核心输入。

---

#### 3.2 AI Validation & Gap Detection（AI 验证与缺陷检测）

- **核心能力**：
  - **Data Quality Validation**：数据质量验证（完整性、一致性）
  - **HBV Gap Detection**：乙型肝炎诊疗流程缺陷检测
    - Testing → Diagnosis → Treatment Gaps（检测 → 诊断 → 治疗中的缺口）

**作用**：利用 AI 识别数据缺失、异常和临床逻辑问题，并专门针对 HBV 患者旅程中的关键缺口（如未检测、未诊断、未治疗）进行量化，支持公共卫生策略和指南制定。

---

#### 3.3 Governance Dashboard（治理仪表盘）

- **核心能力**：
  - **Quality Metrics & HBV Cascade Analytics**：质量指标与 HBV 级联分析
  - **Testing / Diagnosis / Treatment**：检测、诊断、治疗各环节的可视化
  - **Provenance Audit Trail**：溯源审计追踪

**作用**：提供统一的可视化界面，监控数据质量、HBV 诊疗级联和完整的数据溯源链。Provenance Audit Trail 基于哈希锚定，实现从原始数据到分析结果的**端到端可审计**。

---

### 4. 合规性声明（底部）

| 合规项 | 说明 |
|--------|------|
| **GDPR & HIPAA Compliant** | 符合欧盟通用数据保护条例和美国医疗隐私法规 |
| **EU AI Act Ready** | 满足欧盟 AI 法案对高风险 AI 系统的治理要求 |
| **21 CFR Part 11 Audit Trail** | 满足 FDA 对电子记录与电子签名的审计追踪要求 |
| **NO PHI on Blockchain** | 区块链上不存储个人健康信息，仅存储哈希等元数据 |

---

## 三、区块链设计合理性评估

### 3.1 设计模式：哈希上链，数据链下

架构中并未将「区块链」作为独立模块画出，但其思想体现在：

- **AI Validation & Hash Anchoring**：生成并锚定哈希
- **Governance Dashboard → Provenance Audit Trail**：基于哈希的审计追踪
- **NO PHI on Blockchain**：明确区块链仅承载元数据，不承载 PHI

这是一种典型的 **Hash Anchoring（哈希锚定）** 模式：原始数据与 PHI 保留在链下（S3、RDS 等），仅将数据指纹（哈希）写入区块链。

---

### 3.2 合理性分析

| 维度 | 评估 | 说明 |
|------|------|------|
| **隐私保护** | ✅ 合理 | 不将 PHI 上链，避免 GDPR「被遗忘权」、HIPAA 最小必要原则等合规风险；区块链不可篡改与「删除权」的冲突得以规避 |
| **数据完整性** | ✅ 合理 | 哈希是数据的密码学指纹，任何篡改都会导致哈希变化；链上哈希提供不可篡改的完整性证明 |
| **可追溯性** | ✅ 合理 | 对 OMOP 快照、ETL 规范、AI 报告等关键资产锚定哈希，可形成从原始数据到分析结果的完整 Provenance 链 |
| **合规性** | ✅ 合理 | 符合 21 CFR Part 11 对电子记录可审计性的要求，同时兼顾 GDPR、HIPAA、EU AI Act |
| **性能与扩展性** | ✅ 合理 | 大数据集存于 S3/RDS，区块链只承担「验证与信任」职责，避免链上存储海量数据带来的性能瓶颈 |

---

### 3.3 潜在改进点

1. **区块链选型**：图中未明确是公有链、联盟链还是私有链。医疗场景通常采用 **Permissioned Blockchain（许可链）**，便于访问控制和合规审计。
2. **哈希锚定频率**：需明确 OMOP 快照、ETL 规范、AI 报告的锚定时机（如每次 ETL 运行后、每日/每周批量等）。
3. **链上存储内容**：除哈希外，是否还需存储时间戳、数据版本、处理者标识等元数据，以增强审计粒度。

---

## 四、数据流与信任链总结

```
Fragmented RWD (EHR, Lab, Pharmacy, Claims)
        ↓
Secure Data Landing (S3, 加密, 访问控制)
        ↓
ETL & OMOP CDM ←→ PPRL Service
        ↓
AI Validation & Hash Anchoring (哈希生成与锚定)
        ↓
AI Validation & Gap Detection (质量与缺陷检测)
        ↓
Governance Dashboard (质量指标 + HBV 级联 + Provenance Audit Trail)
```

**信任链逻辑**：  
原始数据 → 标准化 → 哈希锚定 → 链上存证 → 审计追踪。  
通过「哈希上链、数据链下」的设计，在保护隐私的前提下，实现数据完整性、可追溯性和监管级审计能力。

---

## 五、结论

RWD TrustChain 架构中的区块链设计采用 **哈希锚定 + 链下数据** 模式，在医疗 RWD 场景下是**合理且成熟**的做法。它既发挥了区块链的不可篡改与可审计优势，又避免了 PHI 上链带来的隐私与合规风险，与 GSK Challenge 文档中「anchoring dataset fingerprints on a permissioned blockchain」的目标一致。

---

*文档生成日期：2026-03-12*
