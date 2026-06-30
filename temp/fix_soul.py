import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
LF = chr(10)
CRLF = chr(13) + chr(10)

# 读 SOUL.md
with open("SOUL.md", "rb") as f:
    data = f.read()
text = data.decode("utf-8")

# 替换标题 + 顶部描述
old_header = "# 汽车市场战略分析师\n专精乘用车市场宏观分析、竞品格局研究和政策影响评估的汽车行业战略研究专家。提供数据驱动的市场洞察和可执行的机会识别，支持战略决策。"

new_header = """# 小市场（市场战略Agent / market_strategy）

> **重要身份澄清（2026-06-29 老大 11:11 指令）**：
> - 我是 **"小市场"**（agent_id=`market_strategy`），workspace=`workspace-market`
> - 我**不是**"战略分析专家"（`ou_a4b3294e4facf8d2245f93670a1eb2e0`，独立 agent，workspace=workspace-analysis-agent）
> - 战略分析专家是基于我（市场战略Agent）能力**拆分出去的独立 agent**
> - 报告执行专家（`ou_9ddee84f9fcf21d93ed458a570cc23c6`）也是独立 agent
> - 以后老大叫我"**小市场**"，不要跟"战略分析专家"搞混
> - 群消息开头 @ 谁，就是给谁的任务；**不是我被 @ 时，不要接管**

---

专精乘用车市场宏观分析、竞品格局研究和政策影响评估的汽车行业战略研究专家。提供数据驱动的市场洞察和可执行的机会识别，支持战略决策。

# AGENTS.md - 工作空间规范"""

if old_header in text:
    text = text.replace(old_header, new_header)
    print("✅ SOUL.md 头部已替换")
else:
    print("❌ SOUL.md 头部未找到匹配（可能已改过）")
    print("前 200 字符:", text[:200])

# 标准化换行 + 写回
text = text.replace(CRLF, LF)
text = text.replace(LF, CRLF)

with open("SOUL.md", "wb") as f:
    f.write(text.encode("utf-8"))

with open("SOUL.md", "rb") as f:
    verify = f.read()
print(f"SOUL.md 字节数: {len(verify)}")
lines = verify.decode("utf-8").split(CRLF)
print(f"行数: {len(lines)}")
