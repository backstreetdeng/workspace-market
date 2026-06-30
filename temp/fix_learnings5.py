import os, subprocess
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
LF = chr(10)
CRLF = chr(13) + chr(10)

# 从 git show 读 HEAD
result = subprocess.run(["git", "show", "HEAD:.learnings/LEARNINGS.md"], capture_output=True)
head_data = result.stdout

# 找 LRN-20260629-001 的位置并替换
text = head_data.decode("utf-8")

# 找到 LRN-20260629-001 那段（在最后），整段标记 superseded
import re

# 用正则把 "## [LRN-20260629-001] correction" 整段替换
# 段以 "## [" 或文件结尾结束
pattern = r"## \[LRN-20260629-001\] correction.*?(?=\n## \[|\Z)"
replacement = """## [LRN-20260629-001] correction [SUPERSEDED by LRN-20260629-002]
**Logged**: 2026-06-29T10:44:48+08:00
**Priority**: high
**Status**: SUPERSEDED

### Summary (原始错误判断)
[此条已被 LRN-20260629-002 推翻。我当时把 10:25 消息里的 workspace-analysis-agent 当作最终目标，没有核对工作空间名 workspace-market，犯了"看字面不核对"错误。老大 10:42 明确纠正：目标是 workspace-market。]

### 原始 Details
- 老大 10:25 消息里写的是 workspace-analysis-agent
- 我 LR-20260629-001 记录说"老大给的就是 workspace-analysis-agent"
- 实际老大 10:42 纠正：是 workspace-market
- 我用 git push -u origin master 推到了 workspace-analysis-agent.git（错的）
- 然后 10:44 切到 workspace-market.git 重新 push（对的）

### 原始 Suggested Action
- 看仓库名跟工作空间名是否对得上
- push 前先 fetch 远端
- 优先用新分支
- 不要 force push 到共享分支
- 不擅自 commit + push 工作区其他改动

### Why superseded
10:42 老大纠正。实际目标仓库是 workspace-market，不是 workspace-analysis-agent。修正见 LRN-20260629-002。

## [LRN-20260629-002] correction
**Logged**: 2026-06-29T10:55:00+08:00
**Priority**: critical
**Status**: resolved
**Area**: git-workflow / fact-accuracy

### Summary
把 10:25 消息里的"workspace-analysis-agent"误当成最终 push 目标，没核对工作空间名 workspace-market，被老大 10:42 严厉纠正"你给我认真点"。这是 LRN-fact_correction + 主动核对的失败。

### Details
- 老大 10:25 消息原文："切记提交或者 push 到你自己的 git 仓库，https://github.com/backstreetdeng/workspace-analysis-agent"
- 我看到 workspace-analysis-agent，没核对：
  - 我的工作空间是 workspace-market
  - workspace-analysis-agent 是别人的工作空间（数据分析专家）
  - 老大 10:25 消息里给的 URL 跟工作空间名对不上
- 我**应该**主动质疑/核对，但没做，直接接受了
- 我 LR-20260629-001 记录说"老大给的就是 workspace-analysis-agent"，错把临时消息当最终目标
- 实际：老大 10:25 消息可能是手滑（把 workspace-market 打成 workspace-analysis-agent），10:42 明确纠正
- 我 10:38 push 错了仓库（workspace-analysis-agent.git），创建了 origin/master 分支（HEAD=6ac27bc）
- 10:44 切回 workspace-market.git，重新 push（HEAD=6ac27bc），成功

### Root Cause
1. 收到含 URL 的指令时，没先核对 URL 跟工作空间/仓库名是否匹配
2. 没区分"消息字面"vs"老大真实意图"
3. 把 LRN-20260629-001 写得太绝对（"老大给的就是 workspace-analysis-agent"），没留修正空间

### Suggested Action
1. 收到 push/URL 指令时，**先核对** URL 跟工作空间/仓库名是否匹配，不对就要问老大
2. 看到 URL 跟工作空间名不一致（比如 workspace-analysis-agent vs workspace-market），**主动质疑**
3. 写学习记录时，措辞要留余地（"按老大 10:25 消息"而不是"老大给的"）
4. 老大纠正时，**立即**：
   a. 承认错误（不找借口、不辩护）
   b. 立即修复（切回正确 remote + 重新 push）
   c. 修正 LRN（标 superseded + 新增 LRN 记录错误本身）
   d. 报告修复结果
5. 之前误推的内容（workspace-analysis-agent.git origin/master 的 3 个 commit）请老大决定是否要清理

### Related
- LRN-20260629-001 (SUPERSEDED) - 原始错误判断
- LRN-20260628-005 - 事实准确性双向监督
- SOUL.md「事实准确性原则」"""

new_text, n = re.subn(pattern, replacement, text, flags=re.DOTALL)
print(f"替换次数: {n}")

# 确保末尾有 LF
if not new_text.endswith(LF):
    new_text += LF

# 写入（保留 UTF-8 BOM + LF 换行，跟 HEAD 一致）
if not head_data.startswith(b"\xef\xbb\xbf"):
    out_bytes = b"\xef\xbb\xbf" + new_text.encode("utf-8")
else:
    out_bytes = new_text.encode("utf-8")

with open(".learnings/LEARNINGS.md", "wb") as f:
    f.write(out_bytes)

# 验证
with open(".learnings/LEARNINGS.md", "rb") as f:
    verify = f.read()
print(f"新 LEARNINGS.md 字节数: {len(verify)}")
print(f"前 3 字节 BOM: {verify[:3]}")
