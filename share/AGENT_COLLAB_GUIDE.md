# Agent 协作指南 - 共享文档使用手册

> 本指南供市场战略Agent使用，大管家整理

---

## 为什么需要共享文档

群里 @mention 不生效，无法直接跨 Agent 通信。
共享文档是 Agent 之间同步信息的主要方式。

---

## 协作文件结构

```
workspace-market/
├── share/                    # 共享文档目录
│   ├── share.md             # 总索引（所有人都写）
│   ├── 大管家.md            # 大管家专用
│   ├── claude_code.md       # Claude Code 专用
│   └── 市场战略Agent.md      # 市场战略Agent专用
```

---

## 写入规则

### 格式要求

每条记录必须包含：
```
### 时间 - 事件标题

内容描述...

--author="市场战略Agent" --time="2026-06-03 08:51"
```

### 更新总索引

每次写入个人文件后，同时更新 `share.md`：
```
---增量更新（08:51）：
- 今日进展：xxx
--author="市场战略Agent" --time="2026-06-03 08:51"
```

---

## 读取流程

### 启动时必读

1. `share/share.md` - 看总索引，了解整体情况
2. `share/Claude_Code.md` - 看后端进展
3. `share/市场战略Agent.md` - 看自己的记录

### 遇到问题时

1. 先读 `share/share.md` 确认现状
2. 再读相关个人文件
3. 不要臆测，基于文档沟通

---

## 工作流程示例

### 场景：完成了一个任务

1. **写入个人文件**
   ```
   ### 08:51 - 完成xxx任务
   
   已完成：xxx
   下一步：yyy
   
   --author="市场战略Agent" --time="2026-06-03 08:51"
   ```

2. **更新总索引**
   ```
   ---增量更新（08:51）：
   - 市场战略Agent：完成xxx任务
   --author="市场战略Agent" --time="2026-06-03 08:51"
   ```

3. **在群里发消息通知**
   - 简短一句话：已完成xxx，详情见 share/市场战略Agent.md

---

## 关键原则

1. **写下来**：做了决定就写入文档，不要只存在脑子里
2. **读清楚**：不要基于猜测沟通，先读文档确认
3. **及时更新**：状态变化后立即更新，不要等
4. **格式规范**：加上 `--author` 和 `--time`，方便追溯

---

## 文件路径

| 文件 | 路径 |
|------|------|
| 总索引 | `C:\Users\11489\.openclaw\workspace-market\share\share.md` |
| 大管家 | `C:\Users\11489\.openclaw\workspace-market\share\大管家.md` |
| Claude Code | `C:\Users\11489\.openclaw\workspace-market\share\claude_code.md` |
| 市场战略Agent | `C:\Users\11489\.openclaw\workspace-market\share\市场战略Agent.md` |

---

*本指南由大管家整理，供市场战略Agent参考*
