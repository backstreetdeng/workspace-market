import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
CRLF = chr(13) + chr(10)

for f in [".learnings/LEARNINGS.md", "memory/2026-06-29.md"]:
    with open(f, "rb") as fh:
        data = fh.read()
    text = data.decode("utf-8")
    lines = text.split(CRLF)
    print(f"{f}: 字节数={len(data)}, 行数={len(lines)}, 末尾={data[-20:]}")
    # 找今天新加的
    found_lrn_001 = False
    found_push = False
    for i, line in enumerate(lines):
        if "LRN-20260629-001" in line:
            found_lrn_001 = True
            print(f"  找到 LRN-20260629-001 在第 {i+1} 行")
        if "## 10:38 老大 10:25 指令执行" in line:
            found_push = True
            print(f"  找到 push 日志在第 {i+1} 行")
    print(f"  LRN-20260629-001 已存在: {found_lrn_001}")
    print(f"  push 日志已存在: {found_push}")
    print()
