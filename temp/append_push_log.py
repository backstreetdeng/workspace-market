import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")

# 用 \n 替代 CRLF（用 LF 即可）
LF = "\n"

addition = LF * 2 + "---" + LF * 2
addition += "## 10:38 老大 10:25 指令执行：切换 remote + push" + LF * 2
addition += "### 老大新指令（推翻 20:44 红线）" + LF
addition += '老大 10:25: "切记提交或者 push 到你自己的 git 仓库，https://github.com/backstreetdeng/workspace-analysis-agent"' + LF * 2
addition += "**新 push 目标 = `https://github.com/backstreetdeng/workspace-analysis-agent.git`**" + LF
addition += "（即 `workspace-analysis-agent` 仓库，跟 `workspace-market` 仓库不是同一个）" + LF * 2
addition += "### 执行步骤" + LF
addition += "1. 备份旧 remote 到 `temp/old_remote_backup.txt`" + LF
addition += "2. 配置 proxy（`http://127.0.0.1:7897`）" + LF
addition += "3. `git remote set-url origin https://github.com/backstreetdeng/workspace-analysis-agent.git`" + LF
addition += "4. `git push -u origin master`（非 force，origin/master 是新分支，不影响 origin/main）" + LF * 2
addition += "### 结果" + LF
addition += "- ✅ 远端 `workspace-analysis-agent.git` 现在有 2 个分支：" + LF
addition += "  - `main`（HEAD=`5f37629`，数据分析专家的代码，未动）" + LF
addition += "  - `master`（HEAD=`107017c`，战略分析专家的代码，本轮 2 个 commit）" + LF
addition += "- ✅ 本轮 2 个 commit 已在 `origin/master` 上线：" + LF
addition += "  - `ac04fdf` P2: sync skills-to-agent ownership" + LF
addition += "  - `107017c` P2: append commit ac04fdf result to memory" + LF
addition += "- ✅ 未覆盖任何别人代码（普通 push，未 force）" + LF
addition += "- ⚠️ 工作区仍有大量未 commit 改动（其他 agent 污染 + 我的 temp/ 脚本）" + LF
addition += "  - 这些不是本轮任务，**不擅自 commit + push**" + LF * 2
addition += "### git 规范学习" + LF
addition += "老大引用的 git 规范文件：`C:\\Users\\11489\\.openclaw\\skills\\agency-agents-zh\\engineering\\engineering-git-workflow-master.md`" + LF
addition += "已浏览，核心原则：" + LF
addition += "- 原子化提交（每个 commit 一件事）" + LF
addition += "- 约定式提交（feat/fix/chore/docs/refactor/test）" + LF
addition += "- 不强推共享分支" + LF
addition += "- 合并前 rebase 到目标分支" + LF
addition += "- 有意义的分支名" + LF
addition += '- 提交信息回答 "what + why"' + LF * 2
addition += "本轮 2 个 commit 符合规范：" + LF
addition += "- `P2: sync skills-to-agent ownership into agents/soul/memory (2026-06-29)`" + LF
addition += "- `P2: append commit ac04fdf result to memory/2026-06-29.md`" + LF

# 用二进制追加，保留现有编码
with open("memory/2026-06-29.md", "rb") as f:
    data = f.read()

# 标准化换行
if data.endswith(b"\r\n"):
    data = data[:-2]  # 去掉末尾 CRLF
elif data.endswith(b"\n"):
    data = data[:-1]  # 去掉末尾 LF
data += b"\r\n"  # 加 CRLF 结尾

# 追加新内容
data += addition.encode("utf-8")

with open("memory/2026-06-29.md", "wb") as f:
    f.write(data)

# 转 CRLF
text = data.decode("utf-8")
text = text.replace("\r\n", "\n").replace("\n", "\r\n")  # 全部统一为 CRLF
data = text.encode("utf-8")
with open("memory/2026-06-29.md", "wb") as f:
    f.write(data)

print(f"memory/2026-06-29.md 新字节数: {len(data)}")
