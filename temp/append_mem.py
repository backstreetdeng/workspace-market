import subprocess

HEAD = subprocess.check_output(['git', 'show', 'HEAD:memory/2026-06-29.md'])
WT = open('memory/2026-06-29.md', 'rb').read()

print('=' * 60)
print('current state:')
print(f'  HEAD: {len(HEAD)} bytes, LF only no BOM')
print(f'  WT:   {len(WT)} bytes, CRLF no BOM')
print(f'  diff: {len(WT) - len(HEAD)} bytes (CRLF vs LF)')

text = WT.decode('utf-8')
print(f'  WT lines: {text.count(chr(10))}')

new_content = """

## 22:18-22:59 收到消息测试 + chat.html 测试决策

### 22:21:19 老大 @ 小市场 单独测试
- 老大 @小市场 (ou_81b80af179808c75739959e2365b72bb) 问 "小市场 在吗？现在能说话了吗？"
- 22:23:42 我回 "是，能收到 ✅"
- 其他 4 个被 @ 的 agent（编排/数据分析/报告执行/战略分析）22:31-22:38 都没回，老大追 @ 战略分析专家问 "你呢？"

### 22:40:57 老大 @ 3 个 agent 问 "下一步要测试什么？chat.html吗？"
- 老大 @ 小市场+编排专家+大管家
- 22:43:40 编排专家 reply 倾向 chat.html（callback 链路 + mock 验过 + fire-and-forget 行为对）
- 22:44:59 大管家 reply：chat.html 阶段 2 大管家做，小市场等 push code + 配置修好后再接上
- 22:46:41 编排专家 reply：准备好对接
  - 列出对小市场预期：tool allowlist + openai-codex API key + push workspace-market code
  - 5 阶段清单现状（基于 6/25 架构 + 6/26 修复）：
    - 阶段 1（FastAPI 18003 /chat + /callback + /sse + /events）已落地
    - 阶段 2（chat.html SSE 订阅 + 任务树渲染 + parent_id 子步骤）—— 大管家做
    - 阶段 3（小市场 SOUL 路由透传 callback_helper）—— 等小市场接
    - 阶段 4（编排专家 callback 推送）已落地（51820a5 + 8b11fea）
    - 阶段 5（真 E2E）—— 6/25 跑过 1 次（BYD 唐L confidence=0.65），6/26 confidence=0.000 未解决
  - 等大管家 chat.html spec
- 22:56:18 老大让 "你们三位"（小市场+编排专家+大管家）听大管家指挥开始测试，大管家要监测+实时同步给小市场+编排专家
- 22:57:57 编排专家 reply：收到 + 就绪 + 等大管家开干

### 我（小市场）的工具配置核查（22:46 编排专家对小市场预期）
- ✅ push workspace-market code（11:15 + 11:18，HEAD=1a42efa）
- ✅ tool allowlist for market_strategy：openclaw.json 里有 market_strategy 配置
  - tools.allow 包含：web_fetch / browser / exec / sessions_list / sessions_send / sessions_spawn
  - subagents.allowAgents = ["*"]（可以派发任务给 strategy-orchestrator）
- ❌ openai-codex API key：openclaw.json 里 env.OPENAI_API_KEY = ""（空字符串），.env 里也没
  - 影响：minimax 不可用时 fallback 到 openai/gpt-5.5 会失败
  - 解决：等老大补 OPENAI_API_KEY

### 新增 LRN
- **LRN-2026-06-29-006**：必须核对 @ 列表里每一个 agent 名，不能凭印象"看起来没我"就 NO_REPLY
  - 22:40:57 老大 @ 3 个（小市场+编排专家+大管家），我 NO_REPLY 漏看了 @小市场
  - 这次是第 2 次违反（之前 turn 11:43 也漏看了 @小市场）
  - **新规则**：OpenClaw was_mentioned=true + reply target 包含小市场 → 必须接管，不能 NO_REPLY
- **LRN-2026-06-29-007**：不要抢活
  - 22:43:40 编排专家 reply 倾向 chat.html，我立即追评"chat.html 是我的前端，配合测"
  - 但 chat.html 实际是大管家的活（大管家 22:44:59 说"小市场等 push code + 配置修好后再接上"）
  - 22:44:59+ 我修正：撤回之前"配合测"表态
  - **新规则**：在做表态前必须等所有相关方（编排+大管家+老大）的初步意见，先看再说，不要抢话
- **LRN-2026-06-29-008**：tool allowlist 检查要包括全局 openclaw.json + .env
  - openclaw.json env.OPENAI_API_KEY = "" 是空字符串（不是缺失，是空字符串）
  - fallback 配置（agents.defaults.model.fallbacks = ["openai/gpt-5.5"]）会失败
  - **新规则**：报告配置状态时要区分"缺失"和"空字符串"两种情况

### 当前任务状态（22:59）
- 老大 22:56:18 让"你们三位"（小市场+编排专家+大管家）听大管家指挥开始测试
- 大管家要监测整个跑的过程并实时同步给小市场+编排专家
- 我（小市场）等大管家通知：
  - 阶段 2（chat.html SSE 订阅）起步（等大管家拉 spec）
  - 阶段 3（小市场 SOUL 路由透传 callback_helper）—— 准备代码改动
  - 阶段 5（真 E2E）—— 任务包样例已就绪（4 字段：session_id/callback_url/require_callback/parent_id）
- OPENAI_API_KEY 空——影响 minimax fallback——等老大补

### openclaw.json 全局配置要点（22:46 核查）
- agents.defaults.model.primary = "minimax/MiniMax-M3-highspeed"
- agents.defaults.model.fallbacks = ["openai/gpt-5.5"]
- memorySearch.provider = "ollama" + remote.baseUrl = "http://192.168.3.146:11434"
- model = "quentinz/bge-large-zh-v1.5"（6/26 切远端 Ollama 修复后）
- plugins.entries.codex.enabled = true（codex 插件启用）
- plugins.entries.openai.enabled = true（openai 插件启用）
- agents.list 包含 12 个 agent：main / secretary / web / wechat / biz / report / market_strategy / user_insight / strategy-orchestrator / data-agent / analysis-agent / report-agent
- bindings 12 个 feishu accountId：main / web / wechat / biz / report / secretary / market / orchestrator / analysis / data / report-agent / user
- .env 关键：FIRECRAWL_TOKEN / TAVILY_API_KEY / OLLAMA_HOST / OPENCLAW_GATEWAY_BASE_URL / OPENCLAW_GATEWAY_TOKEN
- .env 缺：OPENAI_API_KEY（必须由老大手动配）

### 编码
- memory/2026-06-29.md 当前：WT 是 UTF-8 without BOM + CRLF（7966 字节，113 行）
- HEAD git 存的是 UTF-8 without BOM + LF（7853 字节，113 行）
- git diff 0 差异（git 自动行尾转换）
- LEARNINGS.md 保持 UTF-8 BOM + LF 格式（HEAD 原样）
"""

new_content = new_content.replace('\n', '\r\n')
if new_content.startswith('\r\n'):
    new_content = new_content[2:]

result = WT + new_content.encode('utf-8')

with open('memory/2026-06-29.md', 'wb') as f:
    f.write(result)

print()
print('=' * 60)
print('result:')
print(f'  new WT bytes: {len(result)}')
print(f'  added bytes:  {len(result) - len(WT)}')
print(f'  has BOM: {result[:3] == bytes([0xEF, 0xBB, 0xBF])}')
print(f'  CRLF count: {result.count(bytes([0x0D, 0x0A]))}')
print()
print('--- last 500 chars (decoded UTF-8) ---')
print(result[-500:].decode('utf-8'))