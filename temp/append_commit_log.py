import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
CRLF = chr(13) + chr(10)

addition = CRLF + CRLF + "---" + CRLF + CRLF + "## 10:35 commit 完成" + CRLF + CRLF + "- **commit hash**: `ac04fdf`" + CRLF + "- **branch**: master" + CRLF + "- **范围**: 6 files changed, 235 insertions(+), 116 deletions(-)" + CRLF + "- **create mode 100644**: memory/2026-06-29.md (新建)" + CRLF + "- **push 状态**: 未 push（按 20:44 老大红线，待 workspace-market.git 切换指令）" + CRLF + CRLF + "### 群内汇报已发出" + CRLF + "报告 commit hash + 6 个文件清单 + 群规接收确认" + CRLF

with open("memory/2026-06-29.md", "rb") as f:
    data = f.read()
# 末尾加 CRLF（如果不是）再追加
if not data.endswith(b"\r\n"):
    data = data.rstrip(b"\r\n") + b"\r\n"
data += addition.encode("utf-8")
with open("memory/2026-06-29.md", "wb") as f:
    f.write(data)
print(f"memory/2026-06-29.md 新字节数: {len(data)}")
