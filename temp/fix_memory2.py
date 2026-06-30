import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
LF = chr(10)
CRLF = chr(13) + chr(10)

with open("MEMORY.md", "rb") as f:
    data = f.read()
text = data.decode("utf-8")
lines = text.split(CRLF)
print(f"MEMORY.md 总行数: {len(lines)}")
print(f"前 6 行:")
for i in range(6):
    print(f"  {i+1}: {repr(lines[i])}")

# 找 Agent 概述段
# 前 5 行: 标题 + 空 + ## Agent 概述 + bullet1 + bullet2 + bullet3
agent_idx = None
for i, line in enumerate(lines):
    if line.strip() == "## Agent 概述":
        agent_idx = i
        break
print(f"\\n## Agent 概述 在第 {agent_idx+1} 行")

# 替换前 agent_idx+5 行
new_header = """# 小市场（市场战略Agent / market_strategy） - 核心记忆

## Agent 概述
- **Agent ID**: `market_strategy`
- **Agent Name**: 市场战略Agent / 小市场
- **Workspace**: `C:\\Users\\11489\\.openclaw\\workspace-market`
- **角色**: 15年汽车行业市场分析师，精通市场分析、竞品研究、政策解读
- **架构版本**: v2.0（基于215个AI智能体架构优化）

> **2026-06-29 老大 11:11 重要澄清**：
> - 我**不是**\"战略分析专家\"（`ou_a4b3294e4facf8d2245f93670a1eb2e0`，独立 agent，workspace-analysis-agent）
> - 战略分析专家是基于我能力拆分出去的独立 agent
> - 报告执行专家（`ou_9ddee84f9fcf21d93ed458a570cc23c6`）也是独立 agent
> - 以后老大叫我\"**小市场**\"，**不要跟战略分析专家搞混**
> - 群消息开头 @ 谁就是给谁的任务；**不是我被 @ 时，不要接管**

"""

# 找 agent_idx 行后面的内容
# 跳过 "## Agent 概述" 后的 4 个 bullet 行
# lines[0] = 标题, lines[1] = 空, lines[2] = "## Agent 概述", lines[3,4,5] = bullets, lines[6] = 空
# 然后从 lines[7] 开始是原内容
# 让我找下一个 "---" 或 "##" 在 agent_idx 之后的位置
content_start = None
for i in range(agent_idx + 1, len(lines)):
    if lines[i].startswith("---") or lines[i].startswith("##"):
        content_start = i
        break
print(f"Agent 概述后的内容从第 {content_start+1} 行开始: {repr(lines[content_start])}")

# 保留前 agent_idx-0 行的标题（lines[0]），用 new_header 替换 lines[1:content_start]
# lines[0] = "# 汽车市场战略分析师 - 核心记忆" (但我们要换成 "小市场")
new_lines = [new_header] + lines[content_start:]
new_text = CRLF.join(new_lines)
text = new_text.replace(CRLF, LF).replace(LF, CRLF)
with open("MEMORY.md", "wb") as f:
    f.write(text.encode("utf-8"))

with open("MEMORY.md", "rb") as f:
    verify = f.read()
print(f"\nMEMORY.md 新字节数: {len(verify)}")
print(f"新前 15 行:")
new_lines2 = verify.decode("utf-8").split(CRLF)
for i in range(min(15, len(new_lines2))):
    print(f"  {i+1}: {new_lines2[i]}")
