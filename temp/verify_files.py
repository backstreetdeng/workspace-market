import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

print("=== 1. 文件存在 + 编码检查 ===")
files = ["SOUL.md", "MEMORY.md", "agents/competitor-analyst/skill.md", 
         "agents/competitor-analyst/soul.md", "agents/report-generator/skill.md",
         "memory/2026-06-29.md"]
for f in files:
    if os.path.exists(f):
        with open(f, "rb") as fh:
            data = fh.read()
        bom = "UTF-8 BOM" if data[:3] == b"\xef\xbb\xbf" else "无 BOM"
        text = data.decode("utf-8")
        lines = text.split("\r\n")
        print(f"  ✅ {f}: 字节数={len(data)}, 编码={bom}, 行数={len(lines)}")
    else:
        print(f"  ❌ {f}: 不存在")

print("\n=== 2. SOUL.md 末尾确认（v2.2 段已删）===")
with open("SOUL.md", "r", encoding="utf-8") as f:
    soul_lines = f.read().split("\r\n")
print(f"  总行数: {len(soul_lines)}")
for i in range(max(0, len(soul_lines) - 5), len(soul_lines)):
    print(f"  {i+1}: {soul_lines[i]}")
print(f"  包含 v2.2 段? {'是' if any('v2.2' in l for l in soul_lines) else '否（已删除）'}")

print("\n=== 3. MEMORY.md 142-145 行确认 ===")
with open("MEMORY.md", "r", encoding="utf-8") as f:
    mem_lines = f.read().split("\r\n")
for i in range(141, min(146, len(mem_lines))):
    print(f"  {i+1}: {mem_lines[i]}")

print("\n=== 4. agents/competitor-analyst/skill.md 顶部 10 行 ===")
with open("agents/competitor-analyst/skill.md", "r", encoding="utf-8") as f:
    skill_lines = f.read().split("\r\n")
for i in range(min(10, len(skill_lines))):
    print(f"  {i+1}: {skill_lines[i]}")

print("\n=== 5. agents/competitor-analyst/soul.md 顶部 10 行 ===")
with open("agents/competitor-analyst/soul.md", "r", encoding="utf-8") as f:
    soul_agent_lines = f.read().split("\r\n")
for i in range(min(10, len(soul_agent_lines))):
    print(f"  {i+1}: {soul_agent_lines[i]}")

print("\n=== 6. agents/report-generator/skill.md 顶部 10 行 ===")
with open("agents/report-generator/skill.md", "r", encoding="utf-8") as f:
    report_lines = f.read().split("\r\n")
for i in range(min(10, len(report_lines))):
    print(f"  {i+1}: {report_lines[i]}")

print("\n=== 验证完成 ===")
