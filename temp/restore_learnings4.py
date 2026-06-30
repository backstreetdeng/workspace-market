import os, subprocess
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

# 用 git show 读 HEAD 内容
result = subprocess.run(["git", "show", "HEAD:.learnings/LEARNINGS.md"], capture_output=True)
head_data = result.stdout
print("HEAD 字节数:", len(head_data))
print("HEAD 前 30 字节:", head_data[:30])

# 解码
text = head_data.decode("utf-8")
print("HEAD 文本长度:", len(text))
# 看末尾 30 字符
print("HEAD 末尾 30 字符:", repr(text[-30:]))

# 用纯文本添加新条目（用 chr(10) LF 换行）
LF = chr(10)
addition = LF * 2
addition += "## [LRN-20260629-001] correction" + LF
addition += "**Logged**: 2026-06-29T10:44:48+08:00" + LF
addition += "**Priority**: high" + LF
addition += "**Status**: pending" + LF + LF
addition += "### Summary" + LF
addition += "老大 10:25 给的 push 目标 workspace-analysis-agent.git，不是字面意义的'我自己工作空间 workspace-market 的仓库'，是另一个仓库（数据分析专家的）。'你自己'指'你（战略分析专家）的'，但仓库本身是老大指定的。" + LF + LF
addition += "### Details" + LF
addition += "- 工作空间: workspace-market (战略分析专家)" + LF
addition += "- 工作空间 git remote（旧）: https://github.com/backstreetdeng/decision-making.git" + LF
addition += "- 老大 10:25 指令: push 到 https://github.com/backstreetdeng/workspace-analysis-agent （注意仓库名是 workspace-analysis-agent, 跟工作空间名 workspace-market 完全不同）" + LF
addition += "- 远端 workspace-analysis-agent.git 实际 HEAD = 5f37629 (数据分析专家的代码), 不是空的" + LF
addition += "- 我用 git push -u origin master 创建了新分支 master (HEAD=107017c), **不覆盖别人的 main**" + LF + LF
addition += "### Suggested Action" + LF
addition += "- 以后老大说'你自己的 git 仓库'时, 先看仓库名跟工作空间名是否对得上" + LF
addition += "- push 前先 fetch 远端, 看 HEAD 和分支情况" + LF
addition += "- 优先用新分支（避免污染别人的 main）" + LF
addition += "- 不要用 force push 到共享分支" + LF
addition += "- 工作区大量未 commit 改动（其他 agent 污染）不要擅自 commit + push, 等老大 / 大管家决定" + LF

# 确保 text 末尾有 LF
if not text.endswith(LF):
    text += LF

combined = text + addition

# 写入（保留原编码 - UTF-8 BOM + LF 换行，跟 HEAD 一致）
if not head_data.startswith(b"\xef\xbb\xbf"):
    combined_bytes = b"\xef\xbb\xbf" + combined.encode("utf-8")
else:
    combined_bytes = combined.encode("utf-8")

with open(".learnings/LEARNINGS.md", "wb") as f:
    f.write(combined_bytes)

# 验证
with open(".learnings/LEARNINGS.md", "rb") as f:
    verify = f.read()
print("")
print("新 LEARNINGS.md 字节数:", len(verify))
print("前 3 字节 BOM:", verify[:3])
LF_BYTES = bytes([10])
CR_BYTES = bytes([13])
print("LF 数量:", verify.count(LF_BYTES))
print("CRLF 数量:", verify.count(b"\r\n"))
