# -*- coding: utf-8 -*-
"""
FastAPI + SSE 服务 - 纯展示层

设计原则：
1. SSE 仅负责流式展示，不控制任何流程
2. 如果走旧 API 路径，事件来自 workflow_ai_orchestrator.py 兼容适配器
3. 复杂市场分析主线由 strategy-orchestrator 负责自主编排

架构层次：
┌─────────────────────────────────────────────────────────┐
│                    SSE Server (纯展示层)                  │
│                   不控制流程，仅流式输出                    │
└─────────────────────────────────────────────────────────┘
                           ↓ 接收事件
┌─────────────────────────────────────────────────────────┐
│              Legacy Workflow Adapter                      │
│        旧 API / 前端演示兼容路径，不是业务大脑              │
│              (workflow_ai_orchestrator.py)                │
└─────────────────────────────────────────────────────────┘
                           ↓ 调用 Skills
┌─────────────────────────────────────────────────────────┐
│                  OpenClaw Skill System                   │
│              (skill_caller.py / Skills/)                │
└─────────────────────────────────────────────────────────┘
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse


app = FastAPI(
    title="市场战略分析 API",
    version="2.0.0",
    description="""
## 架构说明

本 API 是纯展示层，不控制任何流程。

架构层次：
1. **SSE Server** - 纯展示层，接收并流式输出 Workflow 事件
2. **Legacy Workflow Adapter** - 旧 API / 前端演示兼容路径（workflow_ai_orchestrator.py）
3. **Skill Caller** - OpenClaw Skill 系统调用（skill_caller.py）
4. **Skills** - 专业能力单元（skills/）

复杂市场分析主线：
- 由 `market_strategy_agent` 转交 `strategy-orchestrator`
- `workflows/market_analysis.prose` 是方法论和质量契约，不是流程控制器
    """
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """分析请求"""
    question: str
    context: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "市场战略分析 API",
        "version": "2.0.0",
        "architecture": {
            "layer": "SSE 展示层",
            "legacy_adapter": "workflow_ai_orchestrator.py",
            "main_orchestrator": "strategy-orchestrator",
            "description": "SSE 仅负责流式展示；复杂任务主线由 strategy-orchestrator 编排"
        },
        "endpoints": {
            "analyze": "/analyze",
            "analyze_sse": "/analyze_sse",
            "health": "/health",
            "intent_preview": "/intent_preview"
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "layer": "SSE 展示层",
        "timestamp": time.time()
    }


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    同步分析接口

    注意：这是同步接口，不会返回中间过程。
    如需流式输出，请使用 /analyze_sse
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="question 参数不能为空")

    # 动态导入，避免循环依赖
    try:
        from .workflow_ai_orchestrator import run_market_analysis_ai
    except ImportError:
        from workflow_ai_orchestrator import run_market_analysis_ai

    result = await run_market_analysis_ai(
        question=request.question,
        context=request.context
    )

    return {
        "success": result.get("success", False),
        "data": result,
        "error": result.get("error")
    }


@app.post("/analyze_sse")
async def analyze_sse(request: AnalyzeRequest):
    """
    SSE 格式分析接口 - 纯展示层

    设计原则：
    1. SSE 仅接收并转发 Workflow 的事件
    2. 不控制任何流程逻辑
    3. 当前旧 API 路径由 workflow_ai_orchestrator.py 兼容适配器产出事件

    SSE 事件类型：
    - progress: 阶段进度事件
    - complete: 工作流完成事件
    - error: 错误事件
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="question 参数不能为空")

    # 阶段名称映射
    stages = {
        "planning": "问题规划",
        "stage1": "意图识别",
        "stage2": "数据检索",
        "stage3": "战略分析",
        "stage4": "机会与风险",
        "stage5": "报告生成",
        "quality": "质量检查"
    }

    # 事件队列（异步队列）
    events_queue = asyncio.Queue()

    # 进度回调 - 仅收集事件，不做流程控制
    async def progress_callback(stage: str, status: str, event_data: Dict):
        """
        进度回调函数

        这个函数仅接收 Workflow 推送的事件，
        并将其放入队列供 SSE 发送。

        **重要**：这里不做任何流程控制逻辑！
        """
        summary = _generate_summary(stage, status, event_data)

        sse_event = {
            "stage": stage,
            "stage_name": stages.get(stage, stage),
            "status": status,
            "summary": summary,
            "data": _serialize_data(event_data),
            "timestamp": time.time()
        }

        # 放入队列，等待 SSE 发送
        await events_queue.put(json.dumps(sse_event, ensure_ascii=False))

    async def event_generator():
        """
        SSE 事件发生器

        这是一个纯"观众席"：
        - 接收 Workflow 推送的事件
        - 将事件格式化为 SSE 格式并发送
        - 不控制任何流程
        """
        # 动态导入，避免循环依赖
        try:
            from .workflow_ai_orchestrator import run_market_analysis_ai
        except ImportError:
            from workflow_ai_orchestrator import run_market_analysis_ai

        # 启动 Workflow 任务
        workflow_task = asyncio.create_task(
            run_market_analysis_ai(
                question=request.question,
                context=request.context,
                progress_callback=progress_callback
            )
        )

        # 发送阶段开始事件
        yield {
            "event": "start",
            "data": json.dumps({
                "question": request.question,
                "timestamp": time.time()
            }, ensure_ascii=False)
        }

        # 持续接收事件直到 Workflow 完成
        while not workflow_task.done() or not events_queue.empty():
            try:
                # 等待事件（0.5秒超时）
                event_data_str = await asyncio.wait_for(
                    events_queue.get(),
                    timeout=0.5
                )

                # SSE 格式发送
                yield {
                    "event": "progress",
                    "data": event_data_str
                }

            except asyncio.TimeoutError:
                # 超时继续循环检查 Workflow 状态
                continue

        # 发送剩余事件
        while not events_queue.empty():
            try:
                event_data_str = await asyncio.wait_for(
                    events_queue.get(),
                    timeout=0.1
                )
                yield {
                    "event": "progress",
                    "data": event_data_str
                }
            except asyncio.TimeoutError:
                break

        # 获取最终结果并发送
        try:
            result = await workflow_task

            # 发送完成事件
            complete_event = {
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0),
                "context": {
                    "planning": result.get("context", {}).get("planning", {}),
                    "intent": result.get("context", {}).get("intent", {}),
                    "opportunity_risk": result.get("context", {}).get("opportunity_risk", {})
                },
                "report": result.get("report", {}),
                "quality": result.get("quality", {}),
                "errors": result.get("errors", []),
                "metadata": result.get("metadata", {}),
                "timestamp": time.time()
            }

            yield {
                "event": "complete",
                "data": json.dumps(complete_event, ensure_ascii=False)
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "timestamp": time.time()
                }, ensure_ascii=False)
            }

    return EventSourceResponse(event_generator())


def _serialize_data(data):
    """递归序列化数据为纯 Python 类型"""
    if data is None:
        return None
    if isinstance(data, dict):
        return {k: _serialize_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize_data(item) for item in data]
    if hasattr(data, "to_dict"):
        return data.to_dict()
    if isinstance(data, (str, int, float, bool, type(None))):
        return data
    return str(data)


def _extract_inner_data(data):
    """从包装的数据结构中提取内部数据"""
    if isinstance(data, dict):
        if "data" in data and "summary" in data:
            inner = data.get("data")
            if isinstance(inner, dict):
                return inner
            return data
        return data
    return data


def _generate_summary(stage: str, status: str, data) -> str:
    """
    根据阶段和数据生成摘要文本

    这是展示层的辅助函数，仅用于格式化输出。
    不做任何流程控制决策。
    """
    if status == "running":
        return f"正在 {stages.get(stage, stage)}..."

    if status == "skipped":
        return f"跳过 {stages.get(stage, stage)}"

    if status == "done" and data is None:
        return f"{stages.get(stage, stage)} 完成"

    inner = _extract_inner_data(data)

    # 各阶段的摘要格式化
    if stage == "planning":
        if inner and isinstance(inner, dict):
            intent_type = inner.get("intent_type", "未知")
            skills = inner.get("skills_to_call", [])
            confidence = inner.get("intent_confidence", 0)
            parts = [f"分析类型：{intent_type}"]
            if skills:
                parts.append(f"调用 {len(skills)} 个 Skills")
            if confidence > 0:
                parts.append(f"置信度：{confidence:.0%}")
            return " | ".join(parts)
        return "规划完成"

    elif stage == "stage1":
        if inner and isinstance(inner, dict):
            intent_type = inner.get("intent_type", "未知")
            confidence = inner.get("confidence", 0)
            brands = inner.get("brands_mentioned", [])
            parts = [f"类型：{intent_type}"]
            if confidence > 0:
                parts.append(f"置信度：{confidence:.0%}")
            if brands:
                parts.append(f"品牌：{', '.join(brands[:3])}")
            return " | ".join(parts)
        return "意图识别完成"

    elif stage == "stage2":
        if inner and isinstance(inner, dict):
            parts = []
            vector_count = inner.get("vector_count", 0)
            sql_success = inner.get("sql_success", False)
            if vector_count > 0:
                parts.append(f"向量检索：{vector_count}条")
            if sql_success:
                parts.append("SQL查询：成功")
            return " | ".join(parts) if parts else "数据检索完成"
        return "数据检索完成"

    elif stage == "stage3":
        if inner and isinstance(inner, dict):
            pest = inner.get("pest", {})
            porter = inner.get("porter", {})
            swot = inner.get("swot")
            fourp = inner.get("fourp")

            parts = []
            if pest and pest.get("success"):
                sentiment = pest.get("data", {}).get("summary", {}).get("overall_sentiment", "")
                if sentiment:
                    parts.append(f"PEST：{sentiment}")

            if porter and porter.get("success"):
                attractiveness = porter.get("data", {}).get("summary", {}).get("industry_attractiveness", "")
                if attractiveness:
                    parts.append(f"行业吸引力：{attractiveness}")

            if swot:
                parts.append("SWOT：已完成")

            if fourp:
                parts.append("4P：已完成")

            return " | ".join(parts) if parts else "战略分析完成"
        return "战略分析完成"

    elif stage == "stage4":
        if inner and isinstance(inner, dict):
            opportunities = inner.get("opportunities", [])
            risks = inner.get("risks", [])
            confidence = inner.get("confidence", "未知")

            parts = []
            if opportunities:
                parts.append(f"识别 {len(opportunities)} 个机会")
            if risks:
                parts.append(f"识别 {len(risks)} 个风险")
            parts.append(f"置信度：{confidence}")

            return " | ".join(parts)
        return "机会与风险识别完成"

    elif stage == "stage5":
        if inner and isinstance(inner, dict):
            markdown = inner.get("markdown", "")
            if markdown:
                return f"报告生成完成 ({len(markdown)}字符)"
            success = inner.get("success", False)
            if success:
                return "报告生成完成"
        return "报告生成完成"

    elif stage == "quality":
        if inner and isinstance(inner, dict):
            score = inner.get("quality_score", 0)
            issues = inner.get("issues", [])
            if score >= 70:
                return f"质量评分：{score}/100 ✓"
            else:
                return f"质量评分：{score}/100 ⚠"
        return "质量检查完成"

    return f"{stages.get(stage, stage)} {status}"


@app.get("/intent_preview")
async def intent_preview(question: str):
    """
    意图预览接口

    快速预览用户问题的意图类型，不执行完整分析
    """
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="question 参数不能为空")

    # 使用 Workflow Orchestrator 的 planning 能力
    try:
        from .workflow_ai_orchestrator import OpenProseWorkflowOrchestrator
    except ImportError:
        from workflow_ai_orchestrator import OpenProseWorkflowOrchestrator

    orchestrator = OpenProseWorkflowOrchestrator()
    await orchestrator.initialize()

    # 临时创建 context
    orchestrator.context = None

    # 执行 planning
    result = await orchestrator._execute_planning()

    return {
        "success": True,
        "intent_type": result.get("intent_type", "未知"),
        "confidence": result.get("intent_confidence", 0),
        "brands_mentioned": result.get("brands_mentioned", []),
        "dimensions": result.get("dimensions", []),
        "skills_to_call": result.get("skills_to_call", []),
        "analysis_plan": result.get("analysis_plan", "")
    }


@app.get("/workflow_status")
async def workflow_status():
    """
    获取 Workflow 状态

    查看当前展示层和旧兼容适配器状态
    """
    return {
        "layer": "SSE 展示层",
        "legacy_adapter": "workflow_ai_orchestrator.py",
        "main_orchestrator": "strategy-orchestrator",
        "status": "ready",
        "description": "SSE 仅负责流式展示；复杂任务主线由 strategy-orchestrator 编排"
    }


# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("市场战略分析 API - SSE 展示层")
    print("=" * 60)
    print("架构：SSE 纯展示层")
    print("旧兼容适配器：workflow_ai_orchestrator.py")
    print("复杂任务主线：strategy-orchestrator")
    print("=" * 60)

    uvicorn.run(
        "sse_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
