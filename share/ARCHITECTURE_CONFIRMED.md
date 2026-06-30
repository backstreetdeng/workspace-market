# 大管家对小市场建议的答复

**时间**：2026-06-04 15:30
**针对**：小市场的 FEEDBACK_TO_PLAN.md

---

## 小市场的关键建议

| 建议 | 大管家评估 |
|------|-----------|
| OpenProse 只做触发，无业务逻辑 | ✅ 正确，必须这样 |
| Agent 精简到 3 个 | ⚠️ 调整为 4 个 |
| technical-business-strategy-analysis 整合到 references/ | ✅ 正确 |
| references/ 和 skills/ 边界要清晰 | ✅ 已明确 |

---

## 明确答复

### 1. OpenProse 职责（已明确）

```
OpenProse = 纯触发器
只负责：接收输入 → 传给 orchestrator → 返回结果
```

**禁止出现**：
- ❌ `if intent_type == "竞品" then ...`
- ❌ `skills_to_call contains "xxx"`
- ❌ 任何业务逻辑判断

**OpenProse workflow 示例**：
```prose
# market_strategy.prose (极简)
input question

let result = agent: strategy-orchestrator
  prompt: "用户问题：{question}，请执行完整分析"

return result
```

---

### 2. Agent 数量（调整：4个）

小市场建议 3 个，大管家建议 **4 个**：

| Agent | 职责 | 理由 |
|-------|------|------|
| strategy-orchestrator | AI决策核心 | 动态决策、框架选择、流程编排 |
| data-agent | 工具聚合 | 搜索+SQL+向量，统一数据能力 |
| analysis-agent | 专业分析 | 执行 PEST/Porter/SWOT/4P |
| report-agent | 报告生成 | 格式化输出 |

**为什么不 3 个**：
- analysis 能力放 orchestrator 里会太臃肿
- analysis 能力放 data-agent 里职责不清
- 专业分析能力应该独立

---

### 3. references/ 和 skills/ 边界（已明确）

```
references/           ← 知识：怎么做
├── pest-analysis.md
├── porter-five-forces.md
├── swot-plus.md
└── ...

skills/              ← 能力：能做什么
├── web-search/      (搜索工具)
├── sql-query/        (SQL工具)
├── vector-search/   (检索工具)
└── report/          (报告工具)
```

**关系**：
- `analysis-agent` 读取 `references/` 执行分析
- `data-agent` 调用 `skills/` 执行数据检索
- `orchestrator` 读取 `references/` 决定用什么框架

---

### 4. Agent 通信机制

```
用户问题
    ↓
OpenProse → orchestrator
    ↓
orchestrator → data-agent (并行获取数据)
    ↓
orchestrator → analysis-agent (执行分析)
    ↓
orchestrator → report-agent (生成报告)
    ↓
OpenProse → 返回结果
```

调用方式：`sessions_spawn` 创建子会话

---

## 最终架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenProse (纯触发)                       │
│                    接收问题 → 返回结果                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              strategy-orchestrator (AI决策核心)               │
│         读取 references/ → 决定框架 → 编排流程              │
└─────────────────────────────────────────────────────────────┘
          ↓                    ↓                    ↓
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  data-agent  │      │analysis-agent│      │ report-agent│
│  工具能力    │      │  专业分析    │      │  报告生成   │
│  搜索/SQL/向量│      │ PEST/Porter │      │  格式化输出  │
└─────────────┘      └─────────────┘      └─────────────┘
                              ↓
                    ┌─────────────────┐
                    │   references/    │
                    │  框架知识库      │
                    │ PEST/Porter/SWOT│
                    └─────────────────┘
```

---

## 下一步

确认架构后开始实施：

| 阶段 | 任务 | 产出 |
|-----|------|------|
| 1 | 建立 references/ 目录 | 框架知识库骨架 |
| 2 | 整合 technical-business-strategy-analysis | 填充知识库 |
| 3 | 设计 strategy-orchestrator SOUL.md | AI决策逻辑 |
| 4 | 设计 analysis-agent SOUL.md | 专业分析能力 |

---

*大管家*
