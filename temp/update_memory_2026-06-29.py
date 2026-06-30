# -*- coding: utf-8 -*-
import re
from pathlib import Path

path = Path(r'C:\Users\11489\.openclaw\workspace-market\MEMORY.md')
content = path.read_text(encoding='utf-8')

# === 替换 1: 已安装技能一节 ===
old1 = '''## 已安装技能
- **agent-browser-clawdbot** (2026-06-03) - Vercel Labs 出品，头部浏览器自动化CLI，35k+ stars
- **intent-classifier** - 意图分类
- **pg-vector-search** - 向量知识库检索
- **nl2sql-pg** - 结构化数据库查询
- **automotive-strategy-analysis** → 2026-06-29 已分给战略分析专家，并入 gents/competitor-analyst/（PEST/波特五力/SWOT/4P 框架分析能力）
- **report-generator** → 2026-06-29 已分给报告执行专家，本目录 gents/report-generator/ 保留为协作调用入口'''

new1 = '''## 已安装技能（2026-06-29 working tree 真实状态）
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
- ~~anysearch~~ → 曾存在，已清理'''

if old1 in content:
    content = content.replace(old1, new1)
    print('[1] 已安装技能: 已替换')
else:
    print('[1] 已安装技能: 未找到原文, 跳过')

# === 替换 2: Phase 5 阶段 ===
old2 = '''### Phase 5: 专业 Skills 完善
- [ ] intent-classifier skill
- [ ] pg-vector-search skill
- [ ] nl2sql-pg skill
- [ ] automotive-strategy-analysis skill
- [ ] report-generator skill'''

new2 = '''### Phase 5: 专业 Skills 完善（已迁移完成 2026-06-29）
- [x] intent-classifier skill（market_strategy 入口路由，本地保留）
- [→] pg-vector-search skill → 移交
- [→] nl2sql-pg skill → 移交
- [→] automotive-strategy-analysis skill → 移交战略分析专家
- [→] report-generator skill → 移交报告执行专家'''

if old2 in content:
    content = content.replace(old2, new2)
    print('[2] Phase 5: 已替换')
else:
    print('[2] Phase 5: 未找到原文, 跳过')

# === 追加: 2026-06-29 变更记录 ===
addendum = '''

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
'''

# 防止重复追加
if '## 2026-06-29 架构变更记录' not in content:
    content = content.rstrip() + addendum
    print('[3] 追加 2026-06-29 变更记录: 已追加')
else:
    print('[3] 追加 2026-06-29 变更记录: 已存在, 跳过')

path.write_text(content, encoding='utf-8')
print('MEMORY.md 已写入')