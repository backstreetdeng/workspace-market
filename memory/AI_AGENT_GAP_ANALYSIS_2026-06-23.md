# AI Agent 化差距分析与整改路线图

记录时间：2026-06-23 01:05  
触发原因：用户指出当前系统多次把复杂市场分析做成 Python 工具链，而不是由 `strategy-orchestrator` 自主编排的 AI Agent。

## 一句话结论

当前系统已经有 Agent 架构外壳，也已经把 `python_wrapper` 桥接层切回 `strategy-orchestrator`，但真正的 AI Agent 核心还没有完成：`strategy-orchestrator` 仍有明显的规则编排、占位工具、弱证据过滤和弱反思重规划问题。

这不是“报告格式再优化一点”的问题，而是“业务大脑是否真实存在”的问题。

## 已确认事实

1. `AGENTS.md` 已明确规定：
   - 复杂市场分析、竞品分析、政策影响、趋势研判必须交给 `strategy-orchestrator` 自主编排。
   - `python_wrapper` 只能作为 Skill bridge、SSE/event bridge、上传处理、旧接口兼容和本地工具适配。
   - `python_wrapper` 不允许作为复杂业务流程的大脑。

2. 2026-06-23 00:20 至 00:50 的七步法报告能力一度落在 `python_wrapper/seven_step_report_engine.py` 和 `live_agent_server.py`。
   - 这修好了报告质量问题，但放错了层。
   - 本质上仍然是桥接层顺序跑工具，不是 `strategy-orchestrator` 自主循环。

3. 2026-06-23 00:58 已把 `python_wrapper/live_agent_server.py` 改回薄桥接：
   - `/analyze` 只调用 `market_strategy.orchestrator_integration.run_orchestrated_analysis()`。
   - `/analyze_sse` 只做阶段进度和最终结果推送。
   - `/health` 返回 `mode=sse_relay_to_strategy_orchestrator`。

4. 当前 `strategy-orchestrator` 仍存在核心缺口：
   - `executors/orchestrator.py` 有 ReAct 主循环，但 `_plan()` 仍偏固定任务类型到工具列表的映射。
   - `_replan()` 有回退日志，但没有真正把补救步骤加入后续执行。
   - `_tool_web_search()` 仍是占位，返回“搜索功能待实现”。
   - `_tool_analysis_framework()` 仍是占位，返回“框架分析已完成”。
   - `_tool_rag_retrieve()` 直接检索，缺少品牌、时间、主题、来源质量过滤。
   - `_tool_nl2sql()` 没有接入七步法所需的结构化查询包，无法稳定覆盖月度趋势、同比、车型贡献、价格带、动力类型、竞品份额。
   - 证据账本存在，但证据粒度偏粗，没有形成业务可读的 D/R/W 证据链。
   - 质量门禁存在，但对“品牌错、时间错、RAG 弱相关、报告不可读”的阻断还不够硬。

## 距离真正 AI Agent 的差距

以下是我的工程评估，不是客观打分。

| 能力层 | 当前状态 | 主要差距 | 优先级 |
| --- | --- | --- | --- |
| 架构边界 | 桥接层已切回 relay | 缺少防回退测试，仍可能再次把逻辑写回 bridge | P0 |
| ReAct 主循环 | 有 Plan/Act/Observe/Reflect/Re-plan 外形 | Plan 固定化，Re-plan 不真正生成新行动 | P0 |
| 分析计划 | 七步法里有 analysis_plan，但在 wrapper 层 | 必须下沉到 orchestrator，成为所有工具调用的统一上下文 | P1 |
| 结构化数据 | wrapper 里已有增强 SQL 包 | orchestrator 内部仍只做宽泛 NL2SQL/KB 查询 | P1 |
| RAG 检索 | wrapper 里做过强过滤 | orchestrator RAG 仍可能混入无关文档 | P1 |
| Tavily/外部搜索 | wrapper 里做过来源过滤 | orchestrator web-search 是占位 | P1 |
| 证据链 | EvidenceLedger 存在 | 证据不够业务化，缺少 D/R/W 编号、采纳/剔除原因、URL/日期/来源等级 | P1 |
| 反思与补查 | 有代码结构 | 证据不足、证据冲突、工具失败时没有真实补查链路 | P2 |
| 报告生成 | wrapper 七步法报告质量提升过 | 正式主线 report-agent/orchestrator 输出仍弱 | P2 |
| PPT/洞察卡片 | wrapper 里已有雏形 | 应由 orchestrator 基于证据和洞察卡片生成，而不是模板拼接 | P3 |
| 评测体系 | 只有临时验证 | 缺少小米近半年、比亚迪近12个月、竞品对比、RAG缺失、工具失败等黄金测试集 | P0 |

## 主次顺序

### P0：先防止继续犯架构错误

目标：任何人再把复杂分析逻辑写回 `python_wrapper`，测试必须失败。

验收标准：
- `live_agent_server.py` 不得出现 `LocalSkillBridge`、七步法分析主流程、SQL/RAG/Tavily 顺序调用。
- `/health` 必须暴露 `mode=sse_relay_to_strategy_orchestrator`。
- `/analyze` 结果必须包含真实 `cycles_used`、`stop_reason`、orchestrator trace。
- 新增架构边界测试，避免“trace 写 orchestrator，实际跑 wrapper”的伪调用。

### P1：把七步法能力下沉到 strategy-orchestrator

目标：七步法不是 wrapper 的报告模板，而是 orchestrator 的任务计划、证据管理和质量约束。

必须迁移/重构：
- `analysis_plan`：问题定义、实体、时间、市场范围、假设、所需字段。
- `targeted_sql_pack`：月度趋势、同比、车型贡献、价格带、动力类型、竞品份额。
- `filtered_rag_retrieve`：按品牌、时间、主题、来源质量过滤，并记录 rejected evidence。
- `tavily_web_search`：真实外部补证，带 URL、日期、来源等级、低质量来源过滤。
- `evidence_store`：统一 D/R/W 编号，记录采纳原因、剔除原因、业务支撑点。

验收标准：
- 用户问“小米近半年”，所有工具必须共享“小米 + 最近6个月”。
- 不得出现宋PLUS等非小米车型。
- RAG 弱相关文档必须被剔除，且报告中说明剔除数量和原因。
- 无合格 RAG 时不能假装有证据，必须降低置信度。

### P2：补上真正 Reflect/Re-plan

目标：Agent 不能只按初始步骤跑完，必须能根据证据状态调整下一步。

典型规则：
- 结构化数据缺车型贡献，则补查车型贡献。
- RAG 命中弱相关，则收窄品牌/主题/时间后重查。
- Tavily 无结果，则换 query 或降低外部证据置信度。
- 证据冲突，则交叉验证或把结论降级为假设。
- 关键字段缺失，则报告写“待补证”，而不是模板话术替代数据。

验收标准：
- 每轮 ReAct 输出：计划、行动、观察、缺口、下一步。
- `_replan()` 必须实际产生新增步骤。
- stop_reason 不能只因为有几条证据就提前结束，必须与用户问题覆盖度挂钩。

### P3：把报告变成业务行动系统

目标：报告不是“像报告的文本”，而是业务同事能判断、汇报和行动的战略分析系统。

输出要求：
- 执行摘要。
- 关键结论。
- 结构化数据证据表。
- RAG 证据表。
- Tavily 证据表。
- 竞品矩阵。
- TAM/SAM/SOM。
- SWOT + TOWS。
- Porter 五力。
- 商业模式拆解。
- 洞察卡片。
- 风险与不确定性。
- PPT 基于洞察卡片和证据生成。

验收标准：
- 业务同事先看到结论，再看到证据，不再看到 key=value 原始堆砌。
- 每个关键结论有证据编号和置信度。
- 没有证据编号的内容只能写为假设或待补证。

### P4：建立长期评测和回归机制

目标：不是靠用户“感觉有问题”来发现问题。

黄金测试集：
- 小米汽车最近6个月进入中国新能源市场战略分析。
- 比亚迪最近12个月市场策略分析。
- 比亚迪 vs 特斯拉竞品矩阵。
- 某品牌政策影响分析。
- RAG 不可用时的降级报告。
- Tavily 超时或 SSL 异常时的降级报告。
- 用户指定时间与默认时间冲突时的纠错。

验收标准：
- 每次修改后自动跑核心场景。
- 输出对品牌、时间、车型、证据数量、质量门禁、置信度做断言。
- 失败时不能生成“看起来完整”的报告。

## 第一阶段执行顺序

1. 增加 AGENTS 架构自检规则：发现实现违背职责边界时，必须主动指出并记录，不能等用户发现。
2. 增加桥接层边界测试：证明 `python_wrapper` 只做 relay。
3. 在 `strategy-orchestrator` 中新增 `analysis_plan` 模块。
4. 把 `seven_step_report_engine.py` 中已经验证过的结构化查询、RAG过滤、Tavily过滤、证据编号逻辑拆出并下沉到 orchestrator。
5. 重写 `_replan()`，让它能根据证据缺口产生下一轮工具行动。
6. 再改报告生成和 PPT，而不是先继续美化前端展示。

## 风险提示

- 如果只继续修 `python_wrapper`，短期演示会变好，但正式架构会继续错。
- 如果只做报告模板，业务可读性会提高，但数据和证据仍可能错。
- 如果先做前端，用户会更容易被“看起来顺滑”的流程误导。
- 正确顺序是：边界测试 -> orchestrator 能力下沉 -> 真实反思补查 -> 报告/PPT。

## 当前状态判断

当前系统距离真正 AI Agent 还差一层核心迁移：把已经在 wrapper 里验证过的七步法、证据过滤、结构化查询和报告质量逻辑，迁移到 `strategy-orchestrator`，并让它们受 ReAct 循环控制。

换句话说：桥接层已经不该再当大脑；现在要把大脑补真。
