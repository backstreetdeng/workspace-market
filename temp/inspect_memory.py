# -*- coding: utf-8 -*-
import re
from pathlib import Path

path = Path(r'C:\Users\11489\.openclaw\workspace-market\MEMORY.md')
content = path.read_text(encoding='utf-8')

# 用正则匹配 "## 已安装技能" 段到下一个 "## " 之前
pattern = re.compile(r'## 已安装技能\n.*?(?=\n## |\Z)', re.DOTALL)
m = pattern.search(content)
if m:
    print('--- 原段 ---')
    print(m.group(0))
    print('--- 结束 ---')
else:
    print('未找到段')