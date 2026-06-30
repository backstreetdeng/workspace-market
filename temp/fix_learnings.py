import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
f = ".learnings/LEARNINGS.md"
with open(f, "rb") as fh:
    data = fh.read()
# 统一为 CRLF
text = data.decode("utf-8")
# 先全部转 LF，再转 CRLF
text = text.replace("\r\n", "\n").replace("\n", "\r\n")
data = text.encode("utf-8")
with open(f, "wb") as fh:
    fh.write(data)
# 验证
with open(f, "rb") as fh:
    verify = fh.read()
CRLF = chr(13) + chr(10)
lines = verify.decode("utf-8").split(CRLF)
print(f"{f}: 字节数={len(verify)}, 行数={len(lines)}")
