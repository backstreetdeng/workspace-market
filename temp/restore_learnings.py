import os, subprocess
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

# 从 git HEAD 读出原始 LEARNINGS.md（有换行）
result = subprocess.run(
    ["git", "show", "HEAD:.learnings/LEARNINGS.md"],
    capture_output=True
)
if result.returncode == 0:
    head_data = result.stdout  # bytes
    text = head_data.decode("utf-8")
    print(f"HEAD 字节数: {len(head_data)}")
    print(f"HEAD 行数: {len(text.split(chr(13)+chr(10)))}")
    
    # 添加新条目
    LF = "\n"
    addition = LF * 2 + "## [LRN-20260629-001] correction" + LF
    addition += "**Logged**: 2026-06-29T10:44:48+08:00" + LF
    addition += "**Priority**: high" + LF
    addition += "**Status**: pending" + LF + LF
    addition += "### Summary" + LF
    addition += "老大 10:25 给的 push 目标 workspace-analysis-agent.git，不是字面意义的'我自己工作空间 workspace-market 的仓库'，是另一个仓库（数据分析专家的）。'你自己'指'你（战略分析专家）的'，但仓库本身是老大指定的。" + LF + LF
    addition += "### Details" + LF
    addition += "- 工作空间：workspace-market（战略分析专家）" + LF
    addition += "- 工作空间 git remote（旧）：https://github.com/backstreetdeng/decision-making.git" + LF
    addition += "- 老大 10:25 指令：push 到 https://github.com/backstreetdeng/workspace-analysis-agent（注意仓库名是 workspace-analysis-agent，跟工作空间名 workspace-market 完全不同）" + LF
    addition += "- 远端 workspace-analysis-agent.git 实际 HEAD = 5f37629（数据分析专家的代码），不是空的" + LF
    addition += "- 我用 git push -u origin master 创建了新分支 master（HEAD=107017c），**不覆盖别人的 main**" + LF + LF
    addition += "### Suggested Action" + LF
    addition += "- 以后老大说'你自己的 git 仓库'时，先看仓库名跟工作空间名是否对得上" + LF
    addition += "- push 前先 fetch 远端，看 HEAD 和分支情况" + LF
    addition += "- 优先用新分支（避免污染别人的 main）" + LF
    addition += "- 不要用 force push 到共享分支" + LF
    addition += "- 工作区大量未 commit 改动（其他 agent 污染）不要擅自 commit + push，等老大 / 大管家决定" + LF
    
    # 合并：HEAD 内容 + addition
    # HEAD 内容末尾确保有 CRLF
    if not text.endswith(chr(13)+chr(10)):
        if text.endswith(chr(10)):
            text = text[:-1] + chr(13)+chr(10)
        else:
            text = text + chr(13)+chr(10)
    
    combined = text + addition
    
    # 标准化换行为 CRLF
    combined = combined.replace(chr(13)+chr(10), chr(10))  # 先转 LF
    combined = combined.replace(chr(10), chr(13)+chr(10))  # 再转 CRLF
    
    # 写入文件，保留 UTF-8 BOM
    with open(".learnings/LEARNINGS.md", "wb") as f:
        f.write(b"\xef\xbb\xbf" + combined.encode("utf-8"))
    
    # 验证
    with open(".learnings/LEARNINGS.md", "rb") as f:
        verify = f.read()
    print(f"新 LEARNINGS.md 字节数: {len(verify)}")
    lines = verify.decode("utf-8").split(chr(13)+chr(10))
    print(f"新 LEARNINGS.md 行数: {len(lines)}")
    print(f"前 3 字节 BOM: {verify[:3]}")
else:
    print(f"git show 失败: {result.stderr.decode('utf-8', errors='replace')}")
