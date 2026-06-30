# 后端服务信息 - 供前端对接

**更新时间**: 2026-06-03 09:05
**版本**: v1.1

---

## 服务地址

| 环境 | 地址 |
|------|------|
| 本地开发 | http://localhost:8003 |
| SSE流式接口 | http://localhost:8003/analyze_sse |

---

## API 端点

### 1. 健康检查
`
GET /health
`
响应: {"status": "ok"}

### 2. 同步分析
`
POST /analyze
Content-Type: application/json

{"question": "分析比亚迪市场战略"}
`
响应: 完整分析结果 JSON

### 3. SSE流式分析（推荐）
`
POST /analyze_sse
Content-Type: application/json

{"question": "分析比亚迪市场战略"}
`

### 4. 意图预览
`
GET /intent_preview?question=分析比亚迪
`

---

## 启动命令

`powershell
cd C:\Users\11489\.openclaw\workspace-market\python_wrapper
E:\AI\data\envs\car_agent_env\Scripts\python.exe -m uvicorn sse_server:app --host 0.0.0.0 --port 8003
`

---

## 环境要求

- Python: ai-decision 虚拟环境 (E:\AI\data\envs\car_agent_env\Scripts\python.exe)
- 依赖: pydantic>=2.0, fastapi, uvicorn, sse-starlette

---

## 修复记录

- **v1.1**: 修复 PEST 分析死锁 bug（PEST/Porter 改为串行执行，避免模块导入锁竞争）
- **v1.0**: 初始版本

---

## 下一步

1. 前端连接 SSE 接口
2. 实现进度条展示
3. 实现报告Markdown渲染
