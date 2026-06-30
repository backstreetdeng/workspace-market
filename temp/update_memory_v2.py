# -*- coding: utf-8 -*-
import re
from pathlib import Path

path = Path(r'C:\Users\11489\.openclaw\workspace-market\MEMORY.md')
content = path.read_text(encoding='utf-8')

# 用正则匹配 "## 已安装技能" 段到下一个 "## " 之前
pattern = re.compile(r'## 已安装技能\n.*?(?=\n## |\Z)', re.DOTALL)
new_section = '''## 已安装技能（2026-06-29 working tree 真实状态）
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

m = pattern.search(content)
if m:
    content = content[:m.start()] + new_section + content[m.end():]
    print('[1] 已安装技能: 已整段替换')
else:
    print('[1] 已安装技能: 未找到, 跳过')

path.write_text(content, encoding='utf-8')
print('MEMORY.md 已写入')