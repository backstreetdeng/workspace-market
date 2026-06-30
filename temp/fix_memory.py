import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
LF = chr(10)
CRLF = chr(13) + chr(10)

with open("MEMORY.md", "rb") as f:
    data = f.read()
text = data.decode("utf-8")

# 替换身份描述（顶部）
old_id = "## Agent 概述\n- **Agent ID**: market_strategy_agent\n- **角色**: 15年汽车行业市场分析师，精通市场分析、竞品研究、政策解读\n- **架构版本**: v2.0（基于215个AI智能体架构优化）"

new_id = """## Agent 概述
- **Agent ID**: market_strategy
- **Agent Name**: 市场战略Agent / 小市场
- **Workspace**: `C:\\Users\\11489\\.openclaw\\workspace-market`
- **角色**: 15年汽车行业市场分析师，精通市场分析、竞品研究、政策解读
- **架构版本**: v2.0（基于215个AI智能体架构优化）
- **2026-06-29 老大 11:11 重要澄清**：
  - 我**不是**"战略分析专家"（`ou_a4b3294e4facf8d2245f93670a1eb2e0`，独立 agent，workspace-analysis-agent）
  - 战略分析专家是基于我能力拆分出去的独立 agent
  - 报告执行专家（`ou_9ddee84f9fcf21d93ed458a570cc23c6`）也是独立 agent
  - 以后老大叫我"小市场"，**不要跟战略分析专家搞混**"""

if old_id in text:
    text = text.replace(old_id, new_id)
    print("✅ MEMORY.md 身份段已替换")
else:
    print("❌ MEMORY.md 身份段未找到匹配（可能已改过）")
    print("前 500 字符:", text[:500])

# 标准化换行 + 写回
text = text.replace(CRLF, LF)
text = text.replace(LF, CRLF)

with open("MEMORY.md", "wb") as f:
    f.write(text.encode("utf-8"))

with open("MEMORY.md", "rb") as f:
    verify = f.read()
print(f"MEMORY.md 字节数: {len(verify)}")
