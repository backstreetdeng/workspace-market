import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
CRLF = chr(13) + chr(10)

# 1. SOUL.md 加末尾换行
with open("SOUL.md", "rb") as f:
    data = f.read()
if not data.endswith(b"\r\n"):
    # 确保末尾是 CRLF
    if data.endswith(b"\r"):
        data += b"\n"
    elif data.endswith(b"\n"):
        # LF，需要转换为 CRLF
        data = data[:-1] + b"\r\n"
    else:
        data += b"\r\n"
    with open("SOUL.md", "wb") as f:
        f.write(data)
    print(f"SOUL.md 添加末尾 CRLF，字节数: {len(data)}")
else:
    print("SOUL.md 末尾已有 CRLF")

# 2. 检查所有 6 个文件末尾
files = ["SOUL.md", "MEMORY.md", "agents/competitor-analyst/skill.md", 
         "agents/competitor-analyst/soul.md", "agents/report-generator/skill.md",
         "memory/2026-06-29.md"]
for f in files:
    with open(f, "rb") as fh:
        data = fh.read()
    has_crlf = data.endswith(b"\r\n")
    has_lf = data.endswith(b"\n")
    has_none = not has_lf
    print(f"  {f}: 末尾 CRLF={has_crlf}, LF={has_lf}, 无换行={has_none}")
