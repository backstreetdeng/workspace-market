import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

# 用变量代替字面量
CRLF = chr(13) + chr(10)

print("=== 各文件行数验证 ===")
files = ["SOUL.md", "MEMORY.md", "agents/competitor-analyst/skill.md", 
         "agents/competitor-analyst/soul.md", "agents/report-generator/skill.md",
         "memory/2026-06-29.md"]
for f in files:
    with open(f, "rb") as fh:
        data = fh.read()
    text = data.decode("utf-8")
    lines = text.split(CRLF)
    print(f"  {f}: 字节数={len(data)}, 行数={len(lines)}")

print("\n=== SOUL.md 末尾 6 行 ===")
with open("SOUL.md", "r", encoding="utf-8") as f:
    lines = f.read().split(CRLF)
for i in range(max(0, len(lines) - 6), len(lines)):
    print(f"  {i+1}: {lines[i]}")
print(f"  包含 v2.2 段? {'是' if any('v2.2' in l for l in lines) else '否（已删除）'}")

print("\n=== MEMORY.md 142-145 行 ===")
with open("MEMORY.md", "r", encoding="utf-8") as f:
    lines = f.read().split(CRLF)
for i in range(141, min(146, len(lines))):
    print(f"  {i+1}: {lines[i]}")

print("\n=== agents/competitor-analyst/skill.md 末尾 5 行 ===")
with open("agents/competitor-analyst/skill.md", "r", encoding="utf-8") as f:
    lines = f.read().split(CRLF)
for i in range(max(0, len(lines) - 5), len(lines)):
    print(f"  {i+1}: {lines[i]}")

print("\n=== agents/competitor-analyst/soul.md 末尾 5 行 ===")
with open("agents/competitor-analyst/soul.md", "r", encoding="utf-8") as f:
    lines = f.read().split(CRLF)
for i in range(max(0, len(lines) - 5), len(lines)):
    print(f"  {i+1}: {lines[i]}")

print("\n=== agents/report-generator/skill.md 末尾 5 行 ===")
with open("agents/report-generator/skill.md", "r", encoding="utf-8") as f:
    lines = f.read().split(CRLF)
for i in range(max(0, len(lines) - 5), len(lines)):
    print(f"  {i+1}: {lines[i]}")

print("\n=== memory/2026-06-29.md 末尾 5 行 ===")
with open("memory/2026-06-29.md", "r", encoding="utf-8") as f:
    lines = f.read().split(CRLF)
for i in range(max(0, len(lines) - 5), len(lines)):
    print(f"  {i+1}: {lines[i]}")
