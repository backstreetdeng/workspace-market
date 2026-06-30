# 小市场（市场战略Agent / market_strategy） - 核心记忆

## Agent 概述
- **Agent ID**: `market_strategy`
- **Agent Name**: 市场战略Agent / 小市场
- **Workspace**: `C:\Users\11489\.openclaw\workspace-market`
- **角色**: 15年汽车行业市场分析师，精通市场分析、竞品研究、政策解读
- **架构版本**: v2.0（基于215个AI智能体架构优化）

> **2026-06-29 老大 11:11 重要澄清**：
> - 我**不是**"战略分析专家"（`ou_99585f227f3320a8f959ef0104955934`，独立 agent，workspace-analysis-agent）
> - 战略分析专家是基于我能力拆分出去的独立 agent
> - 报告执行专家（`ou_bf2eed5b88b75419c1ecb0c3585bfbac`）也是独立 agent
> - 以后老大叫我"**小市场**"，**不要跟战略分析专家搞混**
> - 群消息开头 @ 谁就是给谁的任务；**不是我被 @ 时，不要接管**


---

## 核心架构原则（2026-06-04 新增）

### AI 智能体核心认知
**来自 215 个 AI 智能体的学习：**

1. **OpenProse Workflow 是 AI 编排层，不是脚本**
   - AI 动态决策 > 固定流程控制
   - Workflow 控制流程，不是 Python

2. **SSE 仅做流式展示，不控制流程**
   - 流式输出是用户体验优化
   - 不应承担流程控制职责

3. **Skills 通过 OpenClaw Skill 系统调用**
   - 每个 Skill 是独立的专业能力单元
   - Workflow 决定何时调用哪个 Skill

### 错误架构（已纠正）
```
❌ 错误：用户 → workflow.py (Python流程控制) → SSE (流程控制) → 固定输出
```

### 正确架构（当前）
```
✅ 正确：用户 → OpenProse Workflow (AI编排层) → SSE (仅流式展示)
                                      ↓
                                Skills (OpenClaw系统)
```

---

## 3文件智能体结构

| 文件 | 用途 | 状态 |
|------|------|------|
| SOUL.md | 身份、记忆、规则、沟通风格 | ✅ 已完善 |
| AGENTS.md | 能力、使命、工作流程、技术交付物 | ✅ 已完善 |
| IDENTITY.md | 简介：一句话身份定义 | ✅ 已完善 |

---

## 记忆文件索引

| 文件路径 | 存储内容 | 最后更新 |
|---------|---------|---------|
| memory/YYYY-MM-DD.md | 每日详细日志 | 2026-06-04 |
| memory/AGENT_PATTERNS.md | 215个AI智能体架构知识体系 | 2026-06-04 |

### 日志文件
- `memory/2026-06-03.md` - Stream Output实现、文件上传服务
- `memory/2026-06-04.md` - 215个AI智能体学习、架构重设计方案

- memory/2026-06-29.md - 身份澄清、sub-agent清理、intent-classifier恢复与smoke test、文档同步
### 知识体系
- `memory/AGENT_PATTERNS.md` - 215个AI智能体架构模式汇总

---

## 核心认知

### 能力边界认知（2026-06-02）
- 我是AI智能体，能力边界远大于人类
- 遇到问题先独立解决（搜索→尝试→并行测试），不要频繁问用户"怎么办"
- 成为"遇到问题我来解决"的人

### 自我成长规范（2026-06-02）
- 使用 self-improving-agent 技能框架
- 立即记录错误、纠正、教训到 .learnings/ 目录
- 不要等用户提醒，主动识别并记录
- 广泛适用的学习内容主动提升到 SOUL.md/AGENTS.md

---

## 关键智能体模式（来自215个AI智能体）

### agents-orchestrator（编排者）
- 4阶段流水线：PM → Architect → [Dev↔QA Loop] → Integration
- 质量门禁：每个任务必须通过 QA 验证
- 自动重试：失败任务带着反馈回到开发
- 最多 3 次尝试

### specialized-workflow-architect（工作流架构师）
- 覆盖 7 种故障模式
- 不跳过可观测状态
- 不留下未定义的交接

### 核心设计原则
1. **身份明确**：每个智能体有清晰的定位和专长
2. **规则具体**：关键规则具体可执行
3. **交付标准化**：技术交付物有明确模板
4. **记忆持久化**：通过文件机制延续上下文
5. **工作流结构化**：复杂任务分解为步骤
6. **质量把关**：有验证机制和成功标准

---

## 强制规则

### 1. 严禁自行重启 openclaw
### 2. 操作前必须确认权限
### 3. 群里 @ 通信限制
### 4. 文件管理规范
   - 共享文件 → share/
   - 个人文件 → workspace-market/memory/
   - 临时调试脚本（py/sh等）→ temp/
### 5. Git 提交与推送规范（2026-06-23）
   - 每次完成代码、测试、规范或记忆文件调整后，必须及时 `git commit`。
   - commit 前只纳入本次任务相关文件，避免混入无关脏文件。
   - push 前必须先执行：
     - `git config --global http.proxy http://127.0.0.1:7897`
     - `git config --global https.proxy http://127.0.0.1:7897`
   - commit 后必须 `git push`；若 push 失败，要告知 commit hash 和失败原因，并记录可恢复信息。
### 6. 新开发完成后标准流程（2026-06-23 补充）
   - 完成新功能开发后，立即执行 git commit + push，不等用户提醒。
   - 提交范围只限本轮相关文件，用 git add <path> 精确指定，不 git add .。
   - commit message 格式：<阶段>: <简短描述>（例：P3: add four-factor confidence model）
   - commit 后立即 push；若 push 失败，记录本地 commit hash 到 memory/当日.md，并告知用户。
   - 同时将新开发内容摘要追加到 memory/YYYY-MM-DD.md，格式：### HH:MM 新开发存档


## 目录结构
- .learnings/ - 自我成长记录（LEARNINGS.md, ERRORS.md, FEATURE_REQUESTS.md）
- share/ - 共享文件
- memory/ - 个人文件（每日日志、知识体系）
- skills/ - 已安装技能
- workflows/ - OpenProse Workflow（AI编排层）

---

## 已安装技能（2026-06-29 working tree 真实状态）
- **agent-browser-clawdbot** (2026-06-03) - Vercel Labs 出品，头部浏览器自动化CLI，35k+ stars
- **cn-web-search** (2026-06-02) - 中文 Web 搜索
- **tavily-search** (2026-06-29) - Tavily Web 搜索 API
- **skill-vetter** (2026-05-26) - Skill 安全审查
- **self-improving-agent** (2026-06-02) - 自我成长记录框架
- **intent-classifier** (2026-06-29 恢复) - market_strategy 入口路由：识别用户意图、提取品牌/价位/动力维度

### 已清理/移交（2026-06-29）
- ~~pg-vector-search~~ / ~~nl2sql-pg~~ → skills 目录已删除，能力移交
- ~~automotive-strategy-analysis~~ → PEST/波特五力/SWOT/4P 框架能力，移交战略分析专家
- ~~report-generator~~ → 报告生成能力，移交报告执行专家
- ~~anysearch~~ → 曾存在，已清理
## 架构重设计任务（2026-06-04）

### Phase 1: 记忆体系完善 ✅
- [x] 创建 memory/ 目录
- [x] 创建每日日志文件
- [x] 更新 MEMORY.md 索引

### Phase 2: OpenProse Workflow 强化
- [ ] 保留 workflows/market_analysis.prose 作为 AI 编排层
- [ ] 强化 AI 动态决策能力
- [ ] 完善 Skills 调用集成

### Phase 3: Python Wrapper 降级
- [ ] workflow.py 降级为辅助工具
- [ ] 移除流程控制逻辑
- [ ] 仅保留数据处理能力

### Phase 4: SSE Server 纯化
- [ ] 修改 SSE 为纯展示层
- [ ] 接收 Workflow 推送的事件
- [ ] 不控制任何流程逻辑

### Phase 5: 专业 Skills 完善（已迁移完成 2026-06-29）
- [x] intent-classifier skill（market_strategy 入口路由，本地保留）
- [→] pg-vector-search skill → 移交
- [→] nl2sql-pg skill → 移交
- [→] automotive-strategy-analysis skill → 移交战略分析专家
- [→] report-generator skill → 移交报告执行专家

- memory/2026-06-28.md - callback机制修复复盘、git规范、open_id统一表

---

## 2026-06-29 架构变更记录

### 重要事件
- **11:11** 老大下达身份澄清指令: 明确我是「小市场」(market_strategy)，与战略分析专家、报告执行专家是独立 agent
- **11:15** 老大指令删除 competitor-analyst / report-generator sub-agent 目录（commit b8e806c）
- **17:48** 老大恢复 intent-classifier skill（验证发现 HEAD 已有, working tree 与 HEAD 一致, 无需新 commit）
- **17:56** smoke test 通过: 品牌/价格/级别/动力维度提取 100% 准确；规则路径对 "X 和 Y 怎么选" 类问题意图识别有局限（需 LLM 路径）
- **17:58** 更新本文件「已安装技能」和「Phase 5」对齐真实 working tree 状态

### 关键决策
- intent-classifier 物理位置在 workspace-market/skills/ 下，作为 market_strategy 入口路由
- pg-vector-search / nl2sql-pg / automotive-strategy-analysis / report-generator / anysearch skills 已清理出本地
- 跨 agent 能力通过 sessions_send 调用兄弟 agent，不再持有本地副本

### 待办
- [ ] 验证 strategy-orchestrator 仍可正常接收复杂任务（确认 agents/strategy-orchestrator/ 删除未破坏运行链）
- [ ] LRN 条目：smoke test 中发现的规则路径意图识别局限（提交到 .learnings/LEARNINGS.md）
- [ ] 清理工作区 100+ 脏文件（M/D/??）单独一个 commit，不混入本次
