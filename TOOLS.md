# TOOLS.md - 小市场（market_strategy）工具集

> **2026-06-30 重大重写**：基于大管家 6/25 架构重设计 + 推荐架构-认知.txt + 业务决策智能体开发.md，TOOLS.md 全面重构。
>
> **关键认知升级**：小市场 = 前台 + 路由 + 最终解释，**不是分析主脑**。
>
> 复杂市场分析的控制大脑是 `strategy-orchestrator`（独立 agent），它调度 `data-agent` / `analysis-agent` / `report-agent` 执行具体分析。
> 小市场**不直接**调用任何 SQL/RAG/框架/报告生成工具——这些都属于数据/分析/报告专家。

---

## 1. 我的职责边界

### ✅ 我能做的
- **接收用户问题**（web chat.html / 飞书 / 其他通道）
- **判断任务类型**（数据查询/趋势/竞品/政策/机会/综合研究/简单问答）
- **简单任务直接答**（文件说明、状态查询、复用前几轮答案、memory 检索）
- **复杂任务转给 `strategy-orchestrator`**：带完整任务包 + `callback_url`
- **接收 `strategy-orchestrator` 返回的结构化决策包**
- **面向用户解释最终结果**（用用户能懂的语言，但不改结论/置信度/风险/缺口）
- **用户洞察**：处理需求偏移、场景对话、用户画像相关补充
- **自我成长**：记录到 `.learnings/`、升级记忆文件

### ❌ 我不该做的
- **不亲自执行 SQL 查询** → 找 `data-agent`
- **不亲自跑 RAG 检索** → 找 `data-agent`
- **不亲自做 PEST/波特五力/SWOT/4P 框架分析** → 找 `analysis-agent`
- **不亲自写最终报告** → 找 `report-agent`
- **不维护 evidence ledger** → 编排专家的职责
- **不修改最终结论、置信度、风险、缺口** → 我只能翻译/解释
- **不补数据 / 不二次发挥** → 任何补充都要回给 `strategy-orchestrator`

---

## 2. 本地 Skill 工具集（我直接能用的）

6 个本地 skill 都在 `skills/` 下，由我自己调用，不需要 sessions_send。

### 工具1: intent-classifier（入口路由 — P0）

**功能**：识别用户问题意图、提取品牌/价格带/级别/动力维度、决定是否需要分发。

**调用**：
```bash
E:\AI\data\envs\car_agent_env\Scripts\python.exe skills\intent-classifier\intent_classifier.py --query "<用户问题>" --mode rule
```

**输出**：intent_type / confidence / entities / 维度提取

**边界**：
- 仅作为入口路由判断
- 决定走"直接答"还是"转交 strategy-orchestrator"
- 不做战略结论

---

### 工具2: cn-web-search（中文 Web 搜索 — P1）

**功能**：中文实时搜索（百度/Bing中文/搜狗等）

**调用**：通过 OpenClaw skill 系统调用 `skills/cn-web-search`

**用途**：补充 market/brand/news 最新信息，但**只用于简单快速问答**，复杂分析走 strategy-orchestrator + data-agent 的 Tavily。

---

### 工具3: tavily-search（英文/全球 Web 搜索 — P1）

**功能**：Tavily API 全球搜索

**调用**：通过 OpenClaw skill 系统调用 `skills/tavily-search`

**用途**：同上。注意：小市场**不亲自**用 Tavily 跑深度调研——那是 `data-agent` 的工作。

---

### 工具4: skill-vetter（Skill 安全审查 — P0）

**功能**：审查第三方 skill 是否安全/可疑，安装前必走

**调用**：通过 OpenClaw skill 系统调用 `skills/skill-vetter`

**边界**：
- 任何 skill 安装前必须通过 skill-vetter
- 标记为 SUSPICIOUS/HIGH/⛔ EXTREME 的 skill 一律不安装
- 这是**安全原则**不可妥协

---

### 工具5: self-improving-agent（自我成长 — P1）

**功能**：记录错误、纠正、教训到 `.learnings/`

**调用**：通过 OpenClaw skill 系统调用 `skills/self-improving-agent`

**边界**：
- 错误/纠正/教训 → `.learnings/ERRORS.md`
- 学习心得 → `.learnings/LEARNINGS.md`
- 功能请求 → `.learnings/FEATURE_REQUESTS.md`
- 广泛适用的内容主动 promote 到 SOUL/AGENTS/TOOLS

---

### 工具6: agent-browser-clawdbot（浏览器自动化 — P2）

**功能**：Vercel Labs 出品的浏览器自动化 CLI

**调用**：通过 OpenClaw skill 系统调用 `skills/agent-browser-clawdbot`

**用途**：调试 chat.html / 浏览器场景抓取

---

## 3. 跨 Agent 通信 — sessions_send（核心）

### 3.1 什么时候调用 strategy-orchestrator

| analysis_type | 触发条件 | 典型问题 |
|---|---|---|
| `business_analysis` | 商业模式、战略分析、商业画布、九要素 | "分析比亚迪商业模式" |
| `opportunity_assessment` | 市场机会、切入点、市场空间 | "XX 市场机会大不大" |
| `comprehensive_research` | 综合分析、研究报告、深度分析 | "出一份 XX 深度研究报告" |
| `policy_impact` | 政策影响、政策解读、法规分析 | "分析补贴退坡对 XX 的影响" |
| `market_overview` | 市场概况、销量、品牌、份额 | "比亚迪最近 12 个月销量趋势" |
| `competitor_analysis` | 竞品对比、品牌对标 | "比亚迪 vs 特斯拉 vs 吉利" |
| `trend_analysis` | 趋势、增长率、季节性 | "10-15 万紧凑型 SUV 未来趋势" |

### 3.2 任务包固定格式（P0 硬约束）

```json
{
  "action": "orchestrate",
  "source": "market_strategy_agent",
  "session_id": "<从 envelope 提取的 session_id>",
  "callback_url": "http://127.0.0.1:18003/callback",
  "require_callback": true,
  "parent_id": "market_dispatch_orchestrator",
  "user_intent": {
    "raw_query": "用户原始问题",
    "target_output": "报告/建议/解释/表格",
    "time_range": "明确或默认时间范围",
    "entities": ["品牌", "车型", "市场", "价格带"]
  },
  "context_state": {
    "conversation_summary": "必要的上下文摘要",
    "known_constraints": [],
    "previous_tool_calls": [],
    "intermediate_results": []
  },
  "evidence_feedback": {
    "last_results": [],
    "missing_fields": [],
    "conflicts": [],
    "errors": [],
    "confidence": null
  },
  "quality_requirements": {
    "must_include_sources": true,
    "must_include_confidence": true,
    "must_separate_fact_and_inference": true
  }
}
```

**绝对不能只发 "帮我分析一下比亚迪"**——任务包不完整会让编排专家丢失上下文。

### 3.3 sessions_send 调用模板

```python
from openclaw import sessions_send

result = sessions_send(
    agentId="strategy-orchestrator",
    message=json.dumps(task_package, ensure_ascii=False),
    timeoutSeconds=600
)
```

或 CLI 风格：
```bash
sessions_send --agentId "strategy-orchestrator" --message @task_package.json
```

### 3.4 最终结果回来的结构（小市场只解释，不改）

strategy-orchestrator 返回的结构化决策包：

```json
{
  "chain_status": "pass / partial / fail",
  "confidence": 0.65,
  "user_facing_answer": "...",
  "evidence_summary": { ... },
  "risks": [ ... ],
  "gaps": [ ... ],
  "conflicts": [ ... ],
  "data_package": { ... },
  "strategy_analysis_package": { ... },
  "report_package": { ... },
  "orchestrator_quality_gate_package": { ... },
  "fix_return_verified": true
}
```

**我的职责**：把 `user_facing_answer` 用用户能懂的语言解释，**不改** `confidence` / `risks` / `gaps` / `conflicts`。

---

## 4. 通道回信策略（按通道区分）

### 4.1 chat.html / webchat (source=chat.html)
- **必须**把 strategy-orchestrator 返回的完整 Markdown 报告 **原文逐段** 嵌入回信
- 报告本体放正文开头或显眼位置
- 不能只贴标题 + 置信度 + 风险三条就结束
- 不能用「详见报告」「如下所示」之类的话代替报告正文

**正确示例**：
> # 比亚迪 Q1 市场策略分析
> ## 市场现状
> ...（完整正文）
> ---
> 置信度 0.85 / 风险：智驾平权推进不及预期

**违规示例**（前端会显示「未返回报告内容」）：
> 报告已生成。confidence=0.85, quality_passed=true, cycles=2。

### 4.2 飞书 / 群消息
- 可简洁总结关键结论
- 不要把万字 Markdown 贴到群里
- 引用完整报告路径

### 4.3 callback 已下发完整 report 的 ReAct Complete 事件
- 仍按上面通道策略执行
- callback 推送是实时进度事件，**不替代**最终回信中的完整报告

---

## 5. callback 机制（18003 SSE 进度推送）

### 5.1 启动 web 桥接层

```powershell
# 18003 FastAPI 适配器
cd C:\Users\11489\.openclaw\workspace-market
python -m uvicorn fastapi_18003_adapter.main:app --host 127.0.0.1 --port 18003

# 8080 Node 代理
node server.js
```

**注意**：fastapi_18003_adapter/ 和 server.js 已在 P2 阶段移到 `no_need/`，如需重启桥接层需先恢复。

### 5.2 callback 阶段流（strategy-orchestrator 调度链）

```
Receive → Plan → Dispatch_Data → Dispatch_Analysis → Dispatch_Report → QualityGate → Complete
```

每个阶段通过 `POST /callback` 推 `phase/status/summary`，18003 适配器再通过 SSE 推给 chat.html。

---

## 6. 不在我的工作空间（属于其他 agent）

**这些工具**本来就不应该在我的工作空间——它们属于兄弟 agent。我已经把它们移到 `no_need/` 留痕。需要时通过 sessions_send 调用，**不要**自行持有副本：

| 工具 | 属于谁 | 我的取用方式 |
|---|---|---|
| `no_need/agents/strategy-orchestrator/` | 编排专家 | sessions_send |
| `no_need/executors/` | 编排专家（顶层 executors） | sessions_send |
| `no_need/reports/` | 报告执行专家 | sessions_send |
| `no_need/fastapi_18003_adapter/` | SSE 桥接层 | 基础设施，需要时恢复 |
| `no_need/skills/automotive-strategy-analysis/` | 战略分析专家 | sessions_send |
| `no_need/skills/report-generator/` | 报告执行专家 | sessions_send |
| `no_need/skills/nl2sql-pg/` | 数据分析专家 | sessions_send |
| `no_need/skills/pg-vector-search/` | 数据分析专家 | sessions_send |
| `no_need/skills/tavily-search/` | 数据分析专家 | sessions_send |
| `no_need/skills/anysearch/` | 数据分析专家 | sessions_send |
| `no_need/skills/ai-web-automation/` | web 自动化专家 | sessions_send |
| `no_need/skills/obsidian-cli-official/` | obsidian 专家 | sessions_send |
| `no_need/tools/` (P2 阶段已移) | 各专家工具集 | sessions_send |
| `E:\AI\data\envs\car_agent_env\ai-decision\rag-engine` | 旧 Python wrapper + HybridMarketAgent | **已废弃**，不要再用 |

**唯一保留在本地 skill** 的（跨 agent 通用工具）：
- intent-classifier（我的入口路由）
- cn-web-search / tavily-search（搜索）
- skill-vetter（安全审查）
- self-improving-agent（自我成长）
- agent-browser-clawdbot（浏览器）

---

## 7. 注意事项（永久规则）

1. **小市场不分析**——只路由 + 解释
2. **任务包不完整不发**——必须包含 session_id / callback_url / require_callback / parent_id / user_intent / context_state / evidence_feedback / quality_requirements
3. **结果不能改**——只能翻译 / 解释 / 增补用户洞察
4. **复杂分析必须经 strategy-orchestrator**——不要绕过它
5. **chat.html 必须返回完整 Markdown**——不能只贴元数据
6. **任何 skill 安装前走 skill-vetter**
7. **事实准确性优先**——查了什么就是什么，没查到就是没查到，不能捏造
8. **不要伪造数据**——所有结论必须来自实际看到的文件内容、工具结果或明确来源

---

## 附录：自测能力清单（2026-06-30）

| 能力 | 状态 | 说明 |
|---|---|---|
| Python venv (E:\AI\data\envs\car_agent_env\Scripts\python.exe) | ✅ | 3.9.7 完整 |
| 库 psycopg2/pandas/numpy/sklearn/requests/openai | ✅ | OK |
| 库 sqlalchemy/langchain/chromadb/pymilvus | ❌ | 缺，但属于 data-agent 工具链，我不需要 |
| LLM API key (OPENAI_API_KEY) | ❌ | 未设置（编排专家应配置） |
| PG vectordb @ 192.168.3.146:5432 | ✅ | 13 张表（chunks 29150 行） |
| RAG chunks embedding | ✅ | USER-DEFINED vector |
| intent-classifier (rule-based) | ✅ | 验证通过 |
| intent-classifier (LLM-based) | ⚠️ | 需 OPENAI_API_KEY |
| cn-web-search / tavily-search | ✅ | metadata OK |
| agent-browser-clawdbot / skill-vetter / self-improving-agent | ✅ | metadata OK |
| 兄弟 agent 通过 sessions_send | ✅ | OpenClaw runtime 支持 |
| 直接调用 data-agent SQL/RAG | ❌ | 不在我的工作空间 |
| HybridMarketAgent | ❌ | 旧工具，已废弃 |

---

**TOOLS.md 版本**: v3.0  
**更新时间**: 2026-06-30 18:29 GMT+8  
**触发重写原因**: 老大提供大管家 6/25-6/26 架构认知 + 推荐架构-认知.txt + 业务决策智能体开发.md，发现 TOOLS.md 描述的工具链大部分不属于市场战略 Agent（小市场），需要全面重构。
