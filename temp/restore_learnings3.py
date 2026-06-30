import os, subprocess
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

CRLF = b"\r\n"
LF = b"\n"
CR = b"\r"

result = subprocess.run(["git", "show", "HEAD:.learnings/LEARNINGS.md"], capture_output=True)
head_data = result.stdout
print("HEAD 字节数:", len(head_data))
print("HEAD 前 30 字节:", head_data[:30])
print("HEAD 包含 CRLF:", head_data.count(CRLF))
print("HEAD 包含 LF:", head_data.count(LF))
print("HEAD 包含 CR:", head_data.count(CR))

# 新条目
addition = LF * 2 + b"## [LRN-20260629-001] correction" + LF
addition += b"**Logged**: 2026-06-29T10:44:48+08:00" + LF
addition += b"**Priority**: high" + LF
addition += b"**Status**: pending" + LF + LF
addition += b"### Summary" + LF
addition += b"老大 10:25 给的 push 目标 workspace-analysis-agent.git, 不是字面意义的'我自己工作空间 workspace-market 的仓库', 是另一个仓库(数据分析专家的)。'你自己'指'你(战略分析专家)的', 但仓库本身是老大指定的。" + LF + LF
addition += b"### Details" + LF
addition += b"- 工作空间: workspace-market(战略分析专家)" + LF
addition += b"- 工作空间 git remote(旧): https://github.com/backstreetdeng/decision-making.git" + LF
addition += b"- 老大 10:25 指令: push 到 https://github.com/backstreetdeng/workspace-analysis-agent(注意仓库名是 workspace-analysis-agent, 跟工作空间名 workspace-market 完全不同)" + LF
addition += b"- 远端 workspace-analysis-agent.git 实际 HEAD = 5f37629(数据分析专家的代码), 不是空的" + LF
addition += b"- 我用 git push -u origin master 创建了新分支 master(HEAD=107017c), **不覆盖别人的 main**" + LF + LF
addition += b"### Suggested Action" + LF
addition += b"- 以后老大说'你自己的 git 仓库'时, 先看仓库名跟工作空间名是否对得上" + LF
addition += b"- push 前先 fetch 远端, 看 HEAD 和分支情况" + LF
addition += b"- 优先用新分支(避免污染别人的 main)" + LF
addition += b"- 不要用 force push 到共享分支" + LF
addition += b"- 工作区大量未 commit 改动(其他 agent 污染)不要擅自 commit + push, 等老大 / 大管家决定" + LF

if not head_data.endswith(LF):
    head_data += LF

combined = head_data + addition

with open(".learnings/LEARNINGS.md", "wb") as f:
    f.write(combined)

with open(".learnings/LEARNINGS.md", "rb") as f:
    verify = f.read()
print("")
print("新 LEARNINGS.md 字节数:", len(verify))
print("前 3 字节:", verify[:3])
