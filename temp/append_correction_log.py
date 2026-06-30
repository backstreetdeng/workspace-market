import os, subprocess
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
LF = chr(10)
CRLF = chr(13) + chr(10)

result = subprocess.run(["git", "show", "HEAD:memory/2026-06-29.md"], capture_output=True)
text = result.stdout.decode("utf-8")

addition = LF * 2 + "---" + LF * 2
addition += "## 10:44 老大 10:42 纠正：push 目标是 workspace-market（不是 workspace-analysis-agent）" + LF * 2
addition += "### 错误" + LF
addition += "我 10:38 push 时把 10:25 消息里的 workspace-analysis-agent 当成最终目标，没核对工作空间名 workspace-market。实际：老大 10:25 消息里写的就是 workspace-analysis-agent（**可能是手滑**），10:42 老大明确纠正：你给我认真点，应该是 workspace-market。" + LF * 2
addition += "### 修复" + LF
addition += "1. `git remote set-url origin https://github.com/backstreetdeng/workspace-market.git` 切回正确 remote" + LF
addition += "2. `git remote prune origin` 清理 stale 引用" + LF
addition += "3. `git push -u origin master` 重新 push（HEAD=`6ac27bc`，3 个 commit）" + LF
addition += "4. ✅ 远端 `workspace-market.git origin/master` 现在 HEAD=`6ac27bc`" + LF * 2
addition += "### 误推处理" + LF
addition += "之前误推到 `workspace-analysis-agent.git` 的 `origin/master` 分支（HEAD=`6ac27bc`，3 个 commit：ac04fdf/107017c/6ac27bc）—— 这些 commit 仍在别人仓库的 master 分支上。**等老大决定怎么处理**（是删分支还是保留）。" + LF * 2
addition += "### LRN 更新" + LF
addition += "- LRN-20260629-001 标记为 SUPERSEDED" + LF
addition += "- 新增 LRN-20260629-002 记录这次错误" + LF
addition += "- 根因：没核对 URL 跟工作空间名是否匹配" + LF
addition += "- 修正行动：以后收到 push 指令先核对 URL，不一致就问" + LF

# 确保 text 末尾有 LF
if not text.endswith(LF):
    text += LF

combined = text + addition

# 统一为 CRLF
combined = combined.replace(CRLF, LF).replace(LF, CRLF)

with open("memory/2026-06-29.md", "wb") as f:
    f.write(combined.encode("utf-8"))

# 验证
with open("memory/2026-06-29.md", "rb") as f:
    verify = f.read()
print(f"新 memory/2026-06-29.md 字节数: {len(verify)}")
lines = verify.decode("utf-8").split(CRLF)
print(f"行数: {len(lines)}")
