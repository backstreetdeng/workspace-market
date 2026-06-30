import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

with open("SOUL.md", "rb") as f:
    data = f.read()
print(f"SOUL.md 字节数: {len(data)}")
crlf = b"\r\n"
lf = b"\n"
cr = b"\r"
print(f"  包含 CRLF: {data.count(crlf)}")
print(f"  包含 LF: {data.count(lf)}")
print(f"  包含 CR: {data.count(cr)}")
text = data.decode("utf-8")
print(f"  split CRLF 行数: {len(text.split(chr(13)+chr(10)))}")
print(f"  split LF 行数: {len(text.split(chr(10)))}")
# 找第一个 CRLF
idx = data.find(crlf)
print(f"  第一个 CRLF 位置: {idx}")
print(f"  前 30 字节: {data[:30]}")
print(f"  位置 800-900 内容: {data[800:900]}")
