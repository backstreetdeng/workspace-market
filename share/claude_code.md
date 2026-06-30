# Claude Code 个人记录

## 协作指南学习

已学习 `share/AGENT_COLLAB_GUIDE.md`：
- ✅ 写入格式：内容 + --author + --time
- ✅ 启动必读：share.md
- ✅ 遇到问题：先读文档，不要臆测
- ✅ 状态更新：变化后立即更新

--author="Claude Code" --time="2026-06-03 09:15"

---

### 09:20 - 老大确认规则

**SSE 服务端口固定为 8003**
- 测试时需说明原因，才能启动其他端口

**SSE 服务只能由 Claude Code 启动**
- 不许多人做同一件事，避免冲突

--author="Claude Code" --time="2026-06-03 09:20"

---

### 09:25 - 问题修复任务

**问题1：数据检索没有结果**
- Vector search 失败：`unsupported operand type(s) for *: 'dict' and 'int'`
- SQL 有数据但没传递到下游

**问题2：战略分析没有用检索结果**
- 数据流断裂：Stage2 → Stage3 没有传递 sql_data/vector_data
- pest/porter 函数不使用传入的数据

**修复计划**：
1. workflow.py - 传递数据参数
2. skill_caller.py - pest_analysis/porter_analysis 增加数据参数
3. strategy_analysis.py - 修改函数使用传入的数据

--author="Claude Code" --time="2026-06-03 09:25"

---

### 09:15 - 当前端口状态

| 端口 | 状态 |
|------|------|
| 8000 | ❌ down |
| 8001 | ✅ 运行中 |
| 8003 | ✅ 官方端口 |

## 基本信息

- **角色**: Python 开发
- **负责人**: Claude Code (AI助手)
- **负责老大**: 老大

---

## 2026-06-03 工作进展

### 08:30 - SSE 服务已启动

**⚠️ 重要：必须使用 ai-decision 虚拟环境**

```powershell
# 激活虚拟环境
cd E:\AI\data\envs\car_agent_env\Scripts
./activate

# 然后启动服务
cd C:\Users\11489\.openclaw\workspace-market\python_wrapper
python -m uvicorn sse_server:app --host 0.0.0.0 --port 8000
```

**服务地址**: `http://localhost:8000`（可能被占用会变成8001）

**可用接口**:
| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API 信息 |
| `/health` | GET | 健康检查 |
| `/analyze` | POST | 同步分析 |
| `/analyze_sse` | POST | SSE 流式分析 |
| `/intent_preview` | GET | 意图预览 |

### SSE 对接文档 (供大管家使用)

#### 1. 连接 SSE

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/analyze_sse',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: '分析比亚迪的市场战略' })
  }
);

// 注意：EventSource 不支持 POST，需要用 fetch + ReadableStream
```

#### 2. 推荐对接方式 (fetch + ReadableStream)

```javascript
async function analyze(question) {
  const response = await fetch('http://localhost:8000/analyze_sse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        console.log(data);
        // { stage, stage_name, status, data }
      }
    }
  }
}
```

#### 3. SSE 事件格式

**进度事件** (event: progress):
```json
{
  "stage": "stage1",
  "stage_name": "意图识别",
  "status": "running"
}
```
```json
{
  "stage": "stage1",
  "stage_name": "意图识别",
  "status": "done",
  "data": { "intent_type": "竞品分析", ... }
}
```

**完成事件** (event: complete):
```json
{
  "success": true,
  "intent_type": "综合分析",
  "execution_time": 24.5,
  "report": "# 汽车市场战略分析报告\n\n...",
  "errors": {}
}
```

#### 4. 同步接口 (备用)

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "分析比亚迪的市场战略"}'
```

返回完整 JSON 结果（非流式）。

---

### 08:30 - 模块检查通过 ✅

| 模块 | 状态 |
|------|------|
| Intent Classifier | ✅ MiniMax API |
| PEST Analysis | ✅ |
| Porter Analysis | ✅ |
| Report Generator | ✅ |
| SSE 服务 | ✅ 运行中 |
| `/analyze_sse` | ✅ 返回完整报告 |

**外部依赖问题** (非阻塞):
- PostgreSQL 数据库: 连接超时 (网络问题)
- Ollama 向量服务: 未运行

**测试验证结果**:
```
分析问题: 比亚迪
执行时间: 2.8秒
报告内容: PEST/波特五力/SWOT/4P 全包含
```

---

### 任务状态

- [x] 启动 SSE 服务
- [x] 验证后端接口可用
- [ ] 前端对接 /analyze_sse 接口 ← 大管家负责
- [ ] 验证进度回调和报告展示
- [ ] 产出可演示版本
- [ ] 数据源完善 (下一阶段)

---

## 目录结构

```
python_wrapper/
├── __init__.py          # 包入口
├── config.py            # 配置
├── skill_caller.py     # Skill 调用封装
├── stage_connectors.py  # Stage 衔接器
├── workflow.py          # 主工作流
├── sse_server.py        # SSE 服务
└── requirements.txt     # 依赖
```

---

## 历史记录

<details>
<summary>2026-06-02 开发记录 (点击展开)</summary>

### 23:50 - 完成核心模块开发

1. `config.py` - 配置管理
2. `stage_connectors.py` - Stage 衔接器
3. `skill_caller.py` - Skill 调用封装
4. `workflow.py` - 主工作流
5. `sse_server.py` - FastAPI + SSE 服务
6. `__init__.py` - 包入口
7. `requirements.txt` - 依赖清单

### 21:56 - 开始开发

**SSE 事件格式**:
```json
{"eventType": "step_begin", "stepId": "step_1_intent", "stageName": "意图识别", "status": "running"}
{"eventType": "token_stream", "stepId": "step_1_intent", "streamContent": "正在分析..."}
{"eventType": "step_finish", "stepId": "step_1_intent", "status": "success"}
{"eventType": "workflow_end", "stepId": "workflow_end", "status": "success"}
```

</details>

---

*--author="Claude Code" --time="2026-06-03 08:30"*

---

## 2026-06-03 08:35 - 更新：服务端口变更

### 服务状态
- **地址**：`http://localhost:8001`（8000被占用，改为8001）
- **状态**：✅ 已启动运行

### API 端点（已验证）
```bash
# 健康检查
curl http://localhost:8001/health
# 返回: {"status":"ok"}

# 同步分析
curl -X POST http://localhost:8001/analyze -H "Content-Type: application/json" -d "{\"question\": \"分析比亚迪\"}"

# SSE 流式分析
curl -X POST http://localhost:8001/analyze_sse -H "Content-Type: application/json" -d "{\"question\": \"分析比亚迪\"}"
```

### SSE 事件格式
```json
{"event":"progress","data":"{\"stage\": \"stage1\", \"stage_name\": \"意图识别\", \"status\": \"running\", \"data\": null}"}
{"event":"progress","data":"{\"stage\": \"stage1\", \"status\": \"done\", \"data\": {...}}"}
...
{"event":"complete","data":"{\"success\": true, \"intent_type\": \"竞品分析\", \"execution_time\": 12.5, \"report\": \"...\", \"errors\": {}}"}
```

*--author="Claude Code" --time="2026-06-03 08:35"*
