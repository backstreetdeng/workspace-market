import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

files = [
    "agents/competitor-analyst/skill.md",
    "agents/competitor-analyst/soul.md",
    "agents/report-generator/skill.md",
    "memory/2026-06-29.md"
]
LF = chr(10)
CRLF = chr(13) + chr(10)

for f in files:
    with open(f, "rb") as fh:
        data = fh.read()
    text = data.decode("utf-8")
    # 只在内容里替换 LF -> CRLF（不要在代码块内特殊处理，简单替换即可）
    new_text = text.replace(LF, CRLF)
    # 但要避免 \r\n\r\n 重复
    new_text = new_text.replace(CRLF + CRLF, CRLF)
    new_data = new_text.encode("utf-8")
    with open(f, "wb") as fh:
        fh.write(new_data)
    # 验证
    with open(f, "rb") as fh:
        verify = fh.read()
    lines = verify.decode("utf-8").split(CRLF)
    print(f"  {f}: 字节数 {len(data)} -> {len(verify)}, 行数 {len(lines)}")

print("\n=== LF -> CRLF 转换完成 ===")
