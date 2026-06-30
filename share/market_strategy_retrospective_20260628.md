# 战略分析专家（@小市场）E2E Session 复盘

**复盘时间**：2026-06-28 17:25 GMT+8
**E2E 任务**：对比比亚迪与特斯拉 2026 Q1 销量，并分析 Q2 增长策略
**E2E 测试 session**：test_e2e_1782613770（10:29:30 → 10:53:29）

---

## 1. 我在本次任务中的角色定位

我在 `strategy-orchestrator` 编排链路中作为 **下游接收者 + 兜底修复者**，不是分析主执行者。

| 环节 | 执行者 | 我的角色 |
|---|---|---|
| 用户问题分发 | 编排专家（strategy-orchestrator） | 接收回调 |
| 数据查询 / RAG / 框架分析 | 编排专家调度 → 数据分析专家 | 未参与 |
| 报告生成 | 报告执行专家（report_generator.py） | 未参与 |
| 通道回信 / chat.html 渲染 | **我**（market_strategy_agent） | 接收 orchestrator 完整报告 + 嵌入回信 |

---

## 2. Session 内我做了什么

### 2.1 P0 修复（chat.html 拿不到完整 Markdown 报告）

**触发**：大管家 10:29-10:53 跑 chat.html E2E 测试，前端显示「未返回报告内容」。

**根因**：`fastapi_18003_adapter/main.py:_complete_payload` 只从 `gateway_result.get('text')` 提取报告，但 LLM 偶尔只回元数据摘要（confidence/quality_passed/cycles），没有报告本体。

**修复**（双层防御）：
- **代码层**：
  - 新增 `_looks_like_metadata_only_report(text)`：检测 < 600 字符 / 无 Markdown 标题 / 全 backtick 包起来
  - 新增 `_aggregate_report_from_callbacks(session_id, min_length=200)`：从 session_manager 事件历史取最长 report/answer/markdown
  - `_complete_payload` 改 async，新增 `session_id` 参数；metadata-only 时自动聚合替换
- **提示层**：SOUL.md 加「chat.html 回信硬约束」小节（5 必须 + 5 禁止 + 合规/违规示例）

**测试**：`tests/test_fastapi_18003_adapter.py` 加 9 个新单测，**14/14 PASS**

**提交**：
- 本地：`b9bfbb5 P0: aggregate full report from callbacks when gateway text is metadata-only`
- 远端：`ff3ce53..86a8fc8 master -> master`（push 到 decision-making 仓库）

**改动文件**：
- `fastapi_18003_adapter/main.py`（+72 行）
- `SOUL.md`（+34 行）
- `tests/test_fastapi_18003_adapter.py`（+185 行）
- `memory/2026-06-28.md`（+35 行）

---

### 2.2 146 数据库 BYD 2026 销量查询

**触发**：数据分析专家问 BYD 2026 累计销量是否查过 146 本地数据。

**执行**：直连 `192.168.3.146:5432/vectordb/sales_import`（psycopg2 RealDictCursor）

**查询结果**（2026 Jan+Feb 累计）：
| 排名 | 品牌 | 2026 累计（辆） |
|---|---|---|
| 1 | 比亚迪 | **116,235** |
| 2 | 小米 | 59,404 |
| 3 | 丰田 | 58,296 |
| 4 | 吉利 | 56,266 |
| 5 | 赛力斯 | 54,818 |
| 6 | 理想 | 53,481 |

**数据范围**：`sales_import` 表 22502 行，月度格式 YYYYMM，最早 202501、最晚 202602

---

## 3. 调用了哪些工具 / Skill

### 工具
- ✅ `exec`（PowerShell）— 跑 Python + psycopg2 直连 DB
- ✅ `read` / `write` — 改 fastapi_18003_adapter/main.py、SOUL.md、tests
- ✅ `sessions_send` — 群内汇报、向大管家回复
- ❌ `market_data_query.py` — 路径已 DEPRECATED，硬编码 `from market_strategy` 导入断链，未能调通
- ❌ `strategy-orchestrator` — 本次 session 我不是主执行者，未主动调用（编排专家是上游）
- ❌ `HybridMarketAgent` — 同上

### Skill
- ❌ `automotive-strategy-analysis`（PEST / 波特五力 / SWOT / 4P）— 本次 session 未调用（编排链路未走到我这一步）
- ❌ `intent-classifier` / `nl2sql-pg` / `pg-vector-search` / `report-generator` — 同上

---

## 4. 146 本地数据库 + 向量知识库调用情况

| 类别 | 是否调用 | 备注 |
|---|---|---|
| 结构化数据（sales_import） | ✅ 调用 | 直连 psycopg2，绕过 DEPRECATED tool |
| 向量库（policy_documents / documents / chunks） | ❌ 未调用 | 按 SOUL 边界这是数据分析专家职责，本次 session 没需要 |
| 行业报告（RAG） | ❌ 未调用 | 同上 |
| 配置数据（config_data） | ❌ 未调用 | E2E 任务不需要 |

**为什么我没跑向量库**：我作为下游接收者，本次 session 主任务是「修复 chat.html 完整报告渲染」，不是分析任务执行者。146 DB 查询是后来老大追加的，且只需销量数字。

---

## 5. 数据质量问题（我观察到的）

### 5.1 致命问题：品牌字段 mojibake

**现象**：`sales_import.品牌商标` 字段值是 GBK/mojibake 编码，例如 "姣斾簹杩墝"（BYD）。

**影响**：
- 用 `=` 精确匹配 0 行返回
- 用 `LIKE '%BYD%'` 或 `ILIKE '%biyad%'` 全部失败
- 必须用 `SUBSTR(brand, 1, 2) = '姣斾簹'` 模糊匹配才能命中

**建议**：数据治理专家排查 collation，建议升级到 UTF-8 + 加索引 `LOWER(SUBSTR(品牌商标, 1, 2))`。

### 5.2 数据量问题

- `sales_import` 只有 22502 行，覆盖 13 个月（202501-202602）
- 没有 Q1 概念，月份格式是 YYYYMM（202601/202602/202603），BYD Q1 累计 = 202601+202602+202603 三月累加
- 当前 max_d = 202602（2026 Feb），**202603 数据未入库**，无法算完整 Q1 累计

### 5.3 工具链断链

- `market_strategy_DEPRECATED_20260627/` 目录被改名后，`from market_strategy.knowledge_base` 导入全部失败
- `agents/strategy-orchestrator/` 目录在工作树里被删除
- 当前能用的 SQL 数据查询入口只有 `knowledge_base.py` 里的 `MarketKnowledgeBase` 类（需手动重命名目录恢复 import 路径）

### 5.4 字段命名可读性

- 列名是 GBK 乱码（如 `閿€鍞棩鏈?` / `浜у搧鍟嗘爣`），必须查 `information_schema` 或 `pg_attribute` 反查含义
- 建议加列注释或视图别名

---

## 6. 我能/不能做什么（边界声明）

### ✅ 我能做的
- 接收 strategy-orchestrator 的完整报告
- 在 chat.html 通道把完整 Markdown 报告嵌入回信
- 在 feishu 通道做简洁摘要 + 引用报告路径
- 直接 SQL 查 146 数据库（绕过 DEPRECATED 工具链）
- 跨 session 复用昨天的 / 今天的 memory 内容

### ❌ 我不会做的
- 自己跑分析任务（编排专家负责）
- 自己调 RAG / 框架分析 Skill（编排专家负责）
- 自己生成 HTML 报告（报告执行专家负责）
- 改别人的代码（纪律约束，本次也没动过）

---

## 7. 待办

- [ ] 等编排专家修复 complete callback 加 report 字段（外部依赖）
- [ ] 等报告执行专家确认 HTML 报告生成位置（外部依赖）
- [ ] 等编排 + 报告专家修完后，重跑端到端测试做整体验证
- [ ] 数据治理专家解决 mojibake + collation 问题（外部依赖）

---

## 8. 教训沉淀

1. **元数据≠报告**：LLM 偶尔只回元数据摘要，必须双层防御（heuristic + callback aggregation）
2. **工具链断链要主动报**：DEPRECATED 目录没人修，导致我直连 DB，这是架构债
3. **沟通先 @ 再问**：回复时 AT 数据分析专家的 open_id，避免在群里无主提问
4. **git 推送规范**：先 `git config --global http.proxy 7897` → commit → push，push 失败记录 hash

---

## 9. 老大要求的「各自复盘」回应

> 老大原话：每个人把这次执行情况汇总成一个 md 文件，共享到群里

- ✅ 本 md 文件即我的复盘
- ✅ 已发到 `workspace-market/share/` 共享目录
- ⏳ 群内只发摘要 + 路径，不贴万字（遵守 SOUL.md 飞书群简洁原则）

> 老大原话：你们各自看下 session 情况，自己都在这次任务做了什么调用了什么工具和 skill

- ✅ 见本文 §2、§3

> 老大原话：是否调用过 146 服务器本地数据库的结构数据 + 向量知识库

- ✅ 结构数据：调用了（psycopg2 直连 sales_import）
- ❌ 向量知识库：本次未调用（按边界由数据分析专家负责）

> 老大原话：目前数据有什么问题，质量差，数据量少

- ✅ 见本文 §5（mojibake / 工具链断链 / 列名乱码 / 字段缺失）

---

*Author: 战略分析专家（@小市场）*
*Filed: 2026-06-28 17:25 GMT+8*
*Share path: `C:\Users\11489\.openclaw\workspace-market\share\market_strategy_retrospective_20260628.md`*
