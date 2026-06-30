import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
CRLF = b"\r\n"
LF = b"\n"
CR = b"\r"

with open(".learnings/LEARNINGS.md", "rb") as f:
    data = f.read()
print("字节数:", len(data))
print("CRLF 数量:", data.count(CRLF))
print("LF 数量:", data.count(LF))
print("CR 数量:", data.count(CR))
first_lf = data.find(LF)
first_crlf = data.find(CRLF)
print("第一个 LF 位置:", first_lf)
print("第一个 CRLF 位置:", first_crlf)
# 看前 200 字节
print("\n前 300 字节:")
print(repr(data[:300]))
# 看中间 200 字节
print("\n中间 (5000-5300) 字节:")
print(repr(data[5000:5300]))
# 看最后 800 字节
print("\n最后 800 字节:")
print(repr(data[-800:]))
