import os
import sys

WORKSPACE = r"C:\Users\11489\.openclaw\workspace-market"
os.chdir(WORKSPACE)

# 1. SOUL.md - 删除从 "## Skill 内置细粒度 Callback" 开始到文件末尾
with open("SOUL.md", "rb") as f:
    data = f.read()
print(f"SOUL.md 字节数: {len(data)}")
# 找 "## Skill" 字节位置
pattern = "## Skill".encode("utf-8")
idx = data.find(pattern)
print(f"  '## Skill' 位置: {idx}")
if idx > 0:
    # 找到该位置前的 \r\n
    cut_idx = idx
    while cut_idx > 0:
        if data[cut_idx - 1:cut_idx + 1] == b"\r\n":
            cut_idx -= 2
            break
        cut_idx -= 1
    print(f"  截断位置: {cut_idx}")
    new_data = data[:cut_idx]
    with open("SOUL.md", "wb") as f:
        f.write(new_data)
    print(f"  SOUL.md 新字节数: {len(new_data)}")

# 2. MEMORY.md - 修改 143-144 行
with open("MEMORY.md", "rb") as f:
    data = f.read()
text = data.decode("utf-8")
lines = text.split("\r\n")
print(f"\nMEMORY.md 行数: {len(lines)}")
print(f"  143 行（修改前）: {lines[142]}")
print(f"  144 行（修改前）: {lines[143]}")
lines[142] = "- **automotive-strategy-analysis** → 2026-06-29 已分给战略分析专家，并入 `agents/competitor-analyst/`（PEST/波特五力/SWOT/4P 框架分析能力）"
lines[143] = "- **report-generator** → 2026-06-29 已分给报告执行专家，本目录 `agents/report-generator/` 保留为协作调用入口"
new_text = "\r\n".join(lines)
with open("MEMORY.md", "wb") as f:
    f.write(new_text.encode("utf-8"))
print(f"  143 行（修改后）: {lines[142]}")
print(f"  144 行（修改后）: {lines[143]}")
print(f"  MEMORY.md 新字节数: {len(new_text.encode('utf-8'))}")

print("\n=== SOUL.md + MEMORY.md 同步完成 ===")
