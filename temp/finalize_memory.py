# -*- coding: utf-8 -*-
import re
from pathlib import Path
from datetime import datetime

base = Path(r'C:\Users\11489\.openclaw\workspace-market')

# === 1. 创建 memory/2026-06-29.md ===
log_path = base / 'memory' / '2026-06-29.md'
log_content = '''# 2026-06-29 工作日志（小市场 / market_strategy）

## 11:11 老大身份澄清
- 明确我是「小市场」(market_strategy)，workspace = workspace-market
- 与战略分析专家(workspace-analysis-agent) / 报告执行专家 是独立 agent
- 群消息 @ 谁就是给谁的任务；不是被 @ 时不要接管

## 11:15 老大指令删除 sub-agent 目录
- 删除 competitor-analyst / report-generator sub-agent 目录
- git commit: 8e806c P2: 11:15 老大指令 - 改身份为小市场 + 删 competitor-analyst / report-generator sub-agent
- 同步清理 skills/{anysearch, automotive-strategy-analysis, nl2sql-pg, pg-vector-search, report-generator}

## 17:48 老大恢复 intent-classifier skill
- 验证发现 HEAD (e28f828) 已包含 working tree 7 个文件
- 之前误判为「悬空 staged」，实际 HEAD 已 commit，working tree 与 HEAD 一致，无需新 commit
- **教训 (LRN-2026-06-29-003 候选)**: git ls-files 列出文件 ≠ 文件 staged 待 commit，必须配合 git status --short 才能判断是否真有变更
- git commit 失败信息 
o changes added to commit 是最直接的判断信号

## 17:56 intent-classifier smoke test 通过
- 测试问题: 比亚迪和特斯拉在20-30万纯电SUV市场怎么选
- 结果（use_llm=False 规则路径）:
  - 品牌: 比亚迪、特斯拉 都识别 ✅
  - 价格区间: 20-30万 ✅
  - 车型级别: SUV ✅
  - 动力类型: 纯电 ✅
  - 意图分类: fallback 到「综合分析」(confidence 0.5) ⚠️
- **教训 (LRN-2026-06-29-004 候选)**: 规则路径对中文口语化 "X 和 Y 怎么选" / "X 和 Y 哪个好" 识别不到竞品分析；需 LLM 路径（MINIMAX/OpenAI/Ollama）才能正确分类。这是设计预期，不是 bug
- 验证 entry path: E:\\AI\\data\\envs\\car_agent_env\\ai-decision\\rag-engine 仍存在，skill_main.py 里的 sys.path.insert(0, ...) 不会让本地 intent_classifier.py 被覆盖（因为 cd 到本地目录后 cwd 优先）

## 17:58 MEMORY.md 文档同步
- 「已安装技能」节按真实 working tree 状态重写（39 insertions, 15 deletions）
- 「Phase 5」节状态全部更新（[x] / [→]）
- 新增「2026-06-29 架构变更记录」节

## 18:0X git commit + push（计划）
- add 范围: MEMORY.md + memory/2026-06-29.md（仅本轮相关文件）
- commit message: P2: 18:0X 同步 MEMORY.md 到 2026-06-29 真实状态 + 创建当日日志
- push 前必须配置代理 127.0.0.1:7897
'''

if not log_path.exists() or 'identity 澄清' not in log_path.read_text(encoding='utf-8'):
    log_path.write_text(log_content, encoding='utf-8')
    print(f'[1] 创建日志: {log_path.name}')
else:
    print(f'[1] 日志已存在, 跳过')

# === 2. 更新 MEMORY.md 索引 ===
mem_path = base / 'MEMORY.md'
mem_content = mem_path.read_text(encoding='utf-8')

# 用正则匹配「日志文件」子节到下一个 ###  之前
idx_pattern = re.compile(r'(### 日志文件\n- .*?\n)(?=### |\Z)', re.DOTALL)
m = idx_pattern.search(mem_content)
if m:
    print('--- 索引原段 ---')
    print(m.group(0))
    print('--- 结束 ---')
    # 在末尾追加今天的日志
    addition = '- memory/2026-06-29.md - 身份澄清、sub-agent清理、intent-classifier恢复与smoke test、文档同步\n'
    if '2026-06-29.md' not in m.group(0):
        new = m.group(0) + addition
        mem_content = mem_content[:m.start()] + new + mem_content[m.end():]
        print('[2] MEMORY.md 索引: 已追加')
    else:
        print('[2] MEMORY.md 索引: 今日日志已存在, 跳过')
else:
    print('[2] MEMORY.md 索引: 未找到日志段, 跳过')

mem_path.write_text(mem_content, encoding='utf-8')
print('MEMORY.md 已写入')