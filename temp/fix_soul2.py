import os
os.chdir(r"C:\Users\11489\.openclaw\workspace-market")
LF = chr(10)
CRLF = chr(13) + chr(10)

# 1. SOUL.md
with open("SOUL.md", "rb") as f:
    data = f.read()
text = data.decode("utf-8")
lines = text.split(CRLF)
print(f"SOUL.md 总行数: {len(lines)}")
print(f"前 2 行:")
for i in range(2):
    print(f"  {i+1}: {repr(lines[i])}")
print(f"第 3 行: {repr(lines[2])}")

# 替换前 2 行
new_first_two = [
    "# 小市场（市场战略Agent / market_strategy）",
    LF
]
# 旧前 2 行
old_first_two = lines[0] + CRLF + lines[1]
print(f"旧前 2 行: {repr(old_first_two)}")

new_header = """# 小市场（市场战略Agent / market_strategy）

> **重要身份澄清（2026-06-29 老大 11:11 指令）**：
> - 我是 **\"小市场\"**（agent_id=`market_strategy`），workspace=`workspace-market`
> - 我**不是**\"战略分析专家\"（`ou_a4b3294e4facf8d2245f93670a1eb2e0`，独立 agent，workspace=workspace-analysis-agent）
> - 战略分析专家是基于我（市场战略Agent）能力**拆分出去的独立 agent**
> - 报告执行专家（`ou_9ddee84f9fcf21d93ed458a570cc23c6`）也是独立 agent
> - 以后老大叫我\"**小市场**\"，**不要跟战略分析专家搞混**
> - 群消息开头 @ 谁，就是给谁的任务；**不是我被 @ 时，不要接管**

---

"""

# 替换前 2 行 + 加上新头部
rest = CRLF.join(lines[2:])
new_text = new_header + rest

# 写回
text = new_text.replace(CRLF, LF).replace(LF, CRLF)
with open("SOUL.md", "wb") as f:
    f.write(text.encode("utf-8"))
with open("SOUL.md", "rb") as f:
    verify = f.read()
print(f"\nSOUL.md 新字节数: {len(verify)}")
print(f"新前 20 行:")
new_lines = verify.decode("utf-8").split(CRLF)
for i in range(min(20, len(new_lines))):
    print(f"  {i+1}: {new_lines[i]}")
