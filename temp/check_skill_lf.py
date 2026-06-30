import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

with open("agents/competitor-analyst/skill.md", "rb") as f:
    data = f.read()
print(f"字节数: {len(data)}")
crlf = b"\r\n"
lf = b"\n"
print(f"包含 CRLF: {data.count(crlf)}")
print(f"包含 LF: {data.count(lf)}")
# 找第一个换行符位置
idx_crlf = data.find(crlf)
idx_lf = data.find(lf)
print(f"第一个 CRLF 位置: {idx_crlf}")
print(f"第一个 LF 位置: {idx_lf}")
# 用 LF 拆分
text = data.decode("utf-8")
lines = text.split(chr(10))
print(f"split LF 行数: {len(lines)}")
# 看前 5 行
for i in range(5):
    print(f"  行 {i+1}: {lines[i][:80]}")
