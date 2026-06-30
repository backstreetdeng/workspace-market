# 小市场对规划的意见

**时间**：2026-06-04 15:26  
**针对**：大管家写的 IMPLEMENTATION_PLAN.md  

---

## 一、总体评价

✅ **规划方向正确**，三层分离架构清晰，Agent 职责划分合理，references/ 知识库设计很好。

⚠️ **核心担忧**：工作流引擎的混合方案具体实现不明确，需要大管家确认。

---

## 二、关键问题确认

### 1. 【最关键】OpenProse + 智能体编排器的混合方式

**问题**：大管家建议混合，但具体怎么混合没有说明。

**我的理解**：
`
用户问题 
    → OpenProse workflow（纯入口，不做业务决策）
    → strategy-orchestrator（AI 自主决策）
    → 分析 Agents
    → report-agent
`

**关键问题**：
| 问题 | 需要明确 |
|------|---------|
| OpenProse 负责什么？ | 入口？触发？还是固定流程？ |
| 智能体编排器负责什么？ | 动态决策？框架选择？ |
| 两者如何衔接？ | OpenProse 调用 orchestrator？还是 orchestrator 读取 OpenProse？ |

**⚠️ 核心担忧**：如果 OpenProse 包含任何业务逻辑判断，那就是"伪 AI"。真正的 AI 决策必须在 orchestrator 里。

**建议**：OpenProse 只负责：接收输入 → 初始化 context → 调用 orchestrator → 返回结果

---

### 2. 【遗漏】technical-business-strategy-analysis 参考 SKILL

**现状**：规划没有提到这个非常详细的参考 SKILL
- 路径：C:\Users\11489\.openclaw\skills\technical-business-strategy-analysis
- 内容：完整工作流（7个步骤）、数据源配置、错误处理、降级策略

**建议**：把 	echnical-business-strategy-analysis 的内容拆分整合到 references/ 对应文件中

---

### 3. 【需说明】Agent 之间的通信机制

| 问题 | 需要明确 |
|------|---------|
| orchestrator 如何调用 market-analyst？ | sessions_spawn？sessions_send？ |
| 分析 Agents 返回什么格式？ | JSON？Markdown？ |
| orchestrator 如何整合结果？ | AI 自己组合还是固定格式？ |

---

### 4. 【需调整】Python Wrapper Skills 改造策略

| Skill | 现状 | 建议 |
|-------|------|------|
| 
l2sql-pg | Python Wrapper | 改为"AI 理解问题 → 生成 SQL → 执行"的指导 |
| pg-vector-search | Python Wrapper | 改为"AI 判断检索策略"的指导 |
| intent-classifier | Python Wrapper | 保留作为 fallback，不做主流程 |

---

### 5. 【需明确】references/ 和 skills/ 的边界

| 目录 | 内容 | 区别 |
|------|------|------|
| eferences/ | 框架指南 | 知识：怎么做分析 |
| skills/ | 工具调用 | 能力：能做什么 |

**问题**：pest-analysis.md 在 references/ 里，那 skills/pest-analysis/ 还需要吗？

---

## 三、具体建议

### 关于工作流引擎

**建议明确采用"AI 编排 + OpenProse 触发"的混合**：

OpenProse 只负责：
1. 接收用户输入
2. 初始化 context
3. 调用 orchestrator
4. 返回最终结果

**不能有硬编码的流程判断**

---

### 关于 Agent 数量

**建议精简到 3 个 Agent**：

| Agent | 职责 | 理由 |
|-------|------|------|
| strategy-orchestrator | 决策编排（核心） | 必须 |
| data-agent | 工具能力（搜索+SQL+向量） | 工具能力聚合 |
| report-agent | 报告生成 | 输出能力 |

**理由**：当前规模不需要太多独立 Agent，orchestrator 可以统领分析决策。

---

### 关于 technical-business-strategy-analysis 整合

建议作为 references/ 知识库的重要输入：

`
references/
├── pest-analysis.md        # 来自 technical-business-strategy-analysis
├── porter-five-forces.md  # 来自 technical-business-strategy-analysis
├── swot-plus.md          # 来自 technical-business-strategy-analysis
├── 4p-marketing.md       # 来自 technical-business-strategy-analysis
├── tam-sam-som.md        # 来自 technical-business-strategy-analysis
├── competitive-matrix.md  # 来自 technical-business-strategy-analysis
└── data-sources.md       # 来自 technical-business-strategy-analysis
`

---

## 四、请大管家确认

1. [ ] **OpenProse 的具体职责**（只有触发？还是也有引导？不能有业务逻辑）
2. [ ] **orchestrator 的决策逻辑**（如何判断用什么框架？）
3. [ ] **technical-business-strategy-analysis 如何整合**（作为知识输入）
4. [ ] **references/ 和 skills/ 的关系**（是否合并？还是 references 作为 skills 的知识库？）
5. [ ] **Agent 通信机制**（如何调用？如何返回结果？）

---

确认后可以开始第一阶段的实施。

---
*小市场*
