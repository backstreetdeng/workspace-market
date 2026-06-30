# -*- coding: utf-8 -*-
"""
Legacy OpenProse Workflow Adapter
过渡期兼容执行器 - 不是复杂市场分析的业务调度大脑

核心职责：
1. 为旧 API / 前端演示路径保留可运行入口
2. 通过 OpenClaw Skill 系统调用 Skills
3. 将阶段进度转换为 SSE 可展示事件
4. 作为迁移期 adapter，兼容旧的 run_market_analysis_ai() 调用

注意：
- 新架构下，复杂任务自主编排主责属于 strategy-orchestrator。
- 本文件仍包含硬编码阶段逻辑，因此只能视为 legacy adapter / transition executor。
- 后续应逐步把业务决策迁移到持久化 Agent 编排层。
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum


class StageStatus(Enum):
    """工作流阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class WorkflowEvent:
    """工作流事件 - SSE 展示用"""
    stage: str
    status: StageStatus
    summary: str
    data: Any = None
    timestamp: float = None

    def to_sse_dict(self) -> Dict:
        return {
            "stage": self.stage,
            "status": self.status.value,
            "summary": self.summary,
            "data": self.data,
            "timestamp": self.timestamp or time.time()
        }


@dataclass
class WorkflowContext:
    """兼容执行上下文 - 供过渡期 adapter 汇总阶段结果"""
    question: str
    context: Dict[str, Any]

    # 阶段结果存储
    planning_result: Dict = None
    intent_result: Dict = None
    vector_data: Dict = None
    sql_data: Dict = None
    pest_result: Dict = None
    porter_result: Dict = None
    swot_result: Dict = None
    fourp_result: Dict = None
    opportunity_risk: Dict = None
    report: Dict = None

    # 错误跟踪
    errors: List[Dict] = None

    # AI 决策
    skills_to_call: List[str] = None
    skill_order: List[str] = None
    analysis_plan: str = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.skills_to_call is None:
            self.skills_to_call = []
        if self.skill_order is None:
            self.skill_order = []


class OpenProseWorkflowOrchestrator:
    """
    OpenProse Workflow 兼容适配器

    迁移期边界：
    1. 本类为旧 API / 前端演示保留兼容入口。
    2. Skills 通过 OpenClaw Skill 系统调用。
    3. SSE 仅用于流式展示，不控制任何流程。
    4. 复杂市场分析的最终调度大脑是 strategy-orchestrator。
    """

    def __init__(self, workflow_path: str = None):
        self.workflow_path = workflow_path or "workflows/market_analysis.prose"
        self.skill_caller = None  # OpenClaw Skill 调用器
        self.context: Optional[WorkflowContext] = None

    async def initialize(self):
        """初始化 Orchestrator"""
        # 加载 OpenProse Skill 调用器
        try:
            from .skill_caller import get_caller
        except ImportError:
            from skill_caller import get_caller
        self.skill_caller = get_caller()

    async def run(
        self,
        question: str,
        context: Dict[str, Any] = None,
        progress_callback: Callable[[str, str, Dict], None] = None
    ) -> Dict[str, Any]:
        """
        执行旧兼容分析链路

        这是 legacy adapter 的兼容入口：
        1. 保留旧阶段事件，供 SSE / API 演示使用。
        2. 调用 Skills 执行任务。
        3. 返回旧接口期望的报告结构。

        不要把这里当作 v3.0 的复杂任务自主编排入口。
        """
        start_time = time.time()
        self.context = WorkflowContext(question=question, context=context or {})

        # 辅助函数：发送 SSE 事件
        async def emit(stage: str, status: str, summary: str = "", data: Any = None):
            event = WorkflowEvent(
                stage=stage,
                status=StageStatus(status),
                summary=summary,
                data=data
            )
            if progress_callback:
                await progress_callback(stage, status, event.to_sse_dict())

        try:
            # ============================================
            # 阶段0：问题理解与计划（兼容路径的简化规划）
            # ============================================
            await emit("planning", "running", "AI 正在分析问题...")
            planning_result = await self._execute_planning()
            self.context.planning_result = planning_result
            self.context.skills_to_call = planning_result.get("skills_to_call", [])
            self.context.skill_order = planning_result.get("skill_order", [])
            self.context.analysis_plan = planning_result.get("analysis_plan", "")

            await emit("planning", "done",
                      f"分析计划已生成，将调用 {len(self.context.skills_to_call)} 个 Skills",
                      planning_result)

            # ============================================
            # 阶段1：意图识别（可选）
            # ============================================
            if "intent-classifier" in self.context.skills_to_call:
                await emit("stage1", "running", "正在进行意图识别...")
                intent_result = await self._execute_intent_classification()
                self.context.intent_result = intent_result
                await emit("stage1", "done",
                          f"意图识别完成：{intent_result.get('intent_type', '未知')}",
                          intent_result)
            else:
                # 使用 planning 结果作为 intent
                self.context.intent_result = {
                    "intent_type": self.context.planning_result.get("intent_type", "综合分析"),
                    "confidence": self.context.planning_result.get("intent_confidence", 0.8),
                    "brands_mentioned": self.context.planning_result.get("brands_mentioned", []),
                    "dimensions": self.context.planning_result.get("dimensions", [])
                }
                await emit("stage1", "skipped", "意图识别已跳过（由 Planning 阶段覆盖）")

            # ============================================
            # 阶段2：数据检索（动态并行）
            # ============================================
            await emit("stage2", "running", "正在检索数据...")
            await self._execute_data_retrieval()
            await emit("stage2", "done", "数据检索完成", {
                "vector_count": len(self.context.vector_data.get("results", []) if self.context.vector_data else []),
                "sql_success": self.context.sql_data.get("success", False) if self.context.sql_data else False
            })

            # ============================================
            # 阶段3：战略分析（动态执行）
            # ============================================
            await emit("stage3", "running", "正在进行战略分析...")
            await self._execute_strategic_analysis()
            await emit("stage3", "done", "战略分析完成")

            # ============================================
            # 阶段4：机会与风险识别（AI 洞察）
            # ============================================
            await emit("stage4", "running", "正在识别机会与风险...")
            self.context.opportunity_risk = await self._execute_opportunity_risk()
            await emit("stage4", "done", "机会与风险识别完成", self.context.opportunity_risk)

            # ============================================
            # 阶段5：报告生成
            # ============================================
            await emit("stage5", "running", "正在生成报告...")
            self.context.report = await self._execute_report_generation()
            await emit("stage5", "done", "报告生成完成", {"preview": self.context.report.get("markdown", "")[:200]})

            # ============================================
            # 质量门禁检查
            # ============================================
            quality_result = await self._execute_quality_check()
            if quality_result.get("quality_score", 100) < 70:
                # 质量不达标，AI 决定是否重试
                await emit("quality", "warning", f"质量评分: {quality_result['quality_score']}/100，建议重试")

            execution_time = time.time() - start_time

            return {
                "success": True,
                "question": question,
                "execution_time": execution_time,
                "context": {
                    "planning": self.context.planning_result,
                    "intent": self.context.intent_result,
                    "opportunity_risk": self.context.opportunity_risk
                },
                "report": self.context.report,
                "quality": quality_result,
                "errors": self.context.errors,
                "metadata": {
                    "skills_used": self.context.skills_to_call,
                    "skill_order": self.context.skill_order,
                    "timestamp": time.time()
                }
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self.context.errors.append({
                "stage": "orchestrator",
                "error": str(e),
                "timestamp": time.time()
            })
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "context": self.context,
                "errors": self.context.errors
            }

    async def _execute_planning(self) -> Dict[str, Any]:
        """
        阶段0：问题理解与计划
        兼容路径使用简单规则决定需要调用哪些 Skills。

        新架构下，这类决策应由 strategy-orchestrator 基于三层输入和证据反馈完成。
        """
        try:
            # 旧兼容实现使用简单规则；不要继续扩展为业务调度大脑。
            question = self.context.question

            # 简单的意图推断
            intent_type = "综合分析"
            if any(k in question for k in ["趋势", "走势", "预测"]):
                intent_type = "趋势分析"
            elif any(k in question for k in ["竞品", "竞争", "对比"]):
                intent_type = "竞品分析"
            elif any(k in question for k in ["机会", "进入", "投资"]):
                intent_type = "机会识别"
            elif any(k in question for k in ["政策", "补贴", "法规"]):
                intent_type = "政策评估"

            # 品牌识别
            brands = []
            brand_keywords = ["比亚迪", "特斯拉", "吉利", "蔚来", "小鹏", "理想", "小米", "华为"]
            for brand in brand_keywords:
                if brand in question:
                    brands.append(brand)

            # AI 动态决策：需要调用哪些 Skills
            skills_to_call = ["nl2sql-pg"]  # 默认需要结构化数据
            if any(k in question for k in ["政策", "行业", "报告", "背景"]):
                skills_to_call.append("pg-vector-search")

            if len(skills_to_call) > 0:
                skills_to_call.append("automotive-strategy-analysis")

            if len(brands) > 0:
                skills_to_call.extend(["pg-vector-search"])  # 品牌分析需要更多上下文

            # 去重但保持顺序
            skills_to_call = list(dict.fromkeys(skills_to_call))

            return {
                "intent_type": intent_type,
                "intent_confidence": 0.85,
                "brands_mentioned": brands,
                "dimensions": ["规模", "格局", "趋势"],
                "skills_to_call": skills_to_call,
                "skill_order": skills_to_call,
                "analysis_plan": f"基于{intent_type}目标，执行{skills_to_call}技能链",
                "estimated_confidence": 0.8,
                "main_uncertainty": "数据完整性"
            }
        except Exception as e:
            self.context.errors.append({"stage": "planning", "error": str(e)})
            return {
                "intent_type": "综合分析",
                "skills_to_call": ["nl2sql-pg", "pg-vector-search", "automotive-strategy-analysis"],
                "skill_order": ["nl2sql-pg", "pg-vector-search", "automotive-strategy-analysis"]
            }

    async def _execute_intent_classification(self) -> Dict[str, Any]:
        """阶段1：意图分类"""
        try:
            result = await self.skill_caller.classify_intent(self.context.question)
            return result
        except Exception as e:
            self.context.errors.append({"stage": "intent-classification", "error": str(e)})
            return {
                "intent_type": "综合分析",
                "confidence": 0.7,
                "error": str(e)
            }

    async def _execute_data_retrieval(self):
        """阶段2：数据检索（并行）"""
        tasks = []

        # SQL 查询
        if "nl2sql-pg" in self.context.skills_to_call:
            tasks.append(self._retrieve_sql_data())
        else:
            self.context.sql_data = {"success": True, "results": []}

        # 向量检索
        if "pg-vector-search" in self.context.skills_to_call:
            tasks.append(self._retrieve_vector_data())
        else:
            self.context.vector_data = {"success": True, "results": []}

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        if len(results) >= 1:
            result = results[0]
            self.context.sql_data = result if not isinstance(result, Exception) else {
                "success": False, "error": str(result)
            }
        if len(results) >= 2:
            result = results[1]
            self.context.vector_data = result if not isinstance(result, Exception) else {
                "success": False, "error": str(result)
            }

    async def _retrieve_sql_data(self) -> Dict:
        """SQL 数据检索"""
        try:
            return await self.skill_caller.sql_query(
                question=self.context.question,
                execute=True
            )
        except Exception as e:
            self.context.errors.append({"stage": "sql-query", "error": str(e)})
            return {"success": False, "error": str(e)}

    async def _retrieve_vector_data(self) -> Dict:
        """向量数据检索"""
        try:
            return await self.skill_caller.vector_search(
                query=self.context.question,
                top_k=6
            )
        except Exception as e:
            self.context.errors.append({"stage": "vector-search", "error": str(e)})
            return {"success": False, "error": str(e)}

    async def _execute_strategic_analysis(self):
        """阶段3：战略分析"""
        pest_task = self._execute_pest_analysis()
        porter_task = self._execute_porter_analysis()

        pest_result, porter_result = await asyncio.gather(pest_task, porter_task)
        self.context.pest_result = pest_result
        self.context.porter_result = porter_result

        # 品牌特定分析（如果有）
        if self.context.intent_result.get("brands_mentioned"):
            swot_task = self._execute_swot_analysis()
            fourp_task = self._execute_fourp_analysis()
            swot_result, fourp_result = await asyncio.gather(swot_task, fourp_task)
            self.context.swot_result = swot_result
            self.context.fourp_result = fourp_result

    async def _execute_pest_analysis(self) -> Dict:
        """PEST 分析"""
        try:
            brand = self.context.intent_result.get("brands_mentioned", [None])[0]
            return await self.skill_caller.pest_analysis(
                brand=brand,
                sql_data=self.context.sql_data,
                vector_data=self.context.vector_data
            )
        except Exception as e:
            self.context.errors.append({"stage": "pest-analysis", "error": str(e)})
            return {"success": False, "error": str(e)}

    async def _execute_porter_analysis(self) -> Dict:
        """波特五力分析"""
        try:
            brand = self.context.intent_result.get("brands_mentioned", [None])[0]
            return await self.skill_caller.porter_analysis(
                brand=brand,
                sql_data=self.context.sql_data,
                vector_data=self.context.vector_data
            )
        except Exception as e:
            self.context.errors.append({"stage": "porter-analysis", "error": str(e)})
            return {"success": False, "error": str(e)}

    async def _execute_swot_analysis(self) -> Dict:
        """SWOT 分析"""
        try:
            brand = self.context.intent_result.get("brands_mentioned", [None])[0]
            if brand:
                return await self.skill_caller.swot_analysis(
                    brand=brand,
                    sql_data=self.context.sql_data
                )
            return None
        except Exception as e:
            self.context.errors.append({"stage": "swot-analysis", "error": str(e)})
            return {"success": False, "error": str(e)}

    async def _execute_fourp_analysis(self) -> Dict:
        """4P 分析"""
        try:
            brand = self.context.intent_result.get("brands_mentioned", [None])[0]
            if brand:
                return await self.skill_caller.fourp_analysis(
                    brand=brand,
                    sql_data=self.context.sql_data
                )
            return None
        except Exception as e:
            self.context.errors.append({"stage": "fourp-analysis", "error": str(e)})
            return {"success": False, "error": str(e)}

    async def _execute_opportunity_risk(self) -> Dict:
        """阶段4：机会与风险识别"""
        # 这里可以调用 AI 模型进行综合洞察
        # 当前使用简单的规则
        return {
            "opportunities": [
                {
                    "item": "新能源市场持续增长",
                    "scale": "年销800万辆",
                    "confidence": "85%"
                }
            ],
            "risks": [
                {
                    "item": "价格战持续",
                    "probability": "高",
                    "impact": "中"
                }
            ],
            "confidence": "78%",
            "main_uncertainty": "新玩家入场速度"
        }

    async def _execute_report_generation(self) -> Dict:
        """阶段5：报告生成"""
        try:
            return await self.skill_caller.generate_report(
                question=self.context.question,
                intent_type=self.context.intent_result.get("intent_type", "综合分析"),
                pest_result=self.context.pest_result,
                porter_result=self.context.porter_result,
                swot_result=self.context.swot_result,
                fourp_result=self.context.fourp_result,
                vector_results=self.context.vector_data.get("results", []) if self.context.vector_data else [],
                sql_results=self.context.sql_data.get("results", []) if self.context.sql_data else []
            )
        except Exception as e:
            self.context.errors.append({"stage": "report-generation", "error": str(e)})
            return {
                "success": False,
                "error": str(e),
                "markdown": "# 报告生成失败\n\n" + str(e)
            }

    async def _execute_quality_check(self) -> Dict:
        """质量门禁检查"""
        # 简单的质量评估
        error_count = len(self.context.errors)
        total_stages = 5
        failed_stages = len([e for e in self.context.errors if "analysis" in e.get("stage", "") or "generation" in e.get("stage", "")])

        quality_score = max(0, 100 - (error_count * 10) - (failed_stages * 15))

        return {
            "quality_score": quality_score,
            "issues": [
                f"发现 {error_count} 个错误",
                f"其中 {failed_stages} 个关键阶段失败"
            ] if error_count > 0 else [],
            "suggestions": [
                "检查数据源连接",
                "验证 Skill 调用参数"
            ] if error_count > 0 else ["质量良好"]
        }


# 便捷函数
async def run_market_analysis_ai(
    question: str,
    context: Dict[str, Any] = None,
    progress_callback: Callable = None
) -> Dict[str, Any]:
    """运行旧兼容市场分析链路。复杂任务主线应交给 strategy-orchestrator。"""
    orchestrator = OpenProseWorkflowOrchestrator()
    await orchestrator.initialize()
    return await orchestrator.run(question, context, progress_callback)


# 测试
if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("Legacy OpenProse Workflow Adapter Test")
        print("=" * 60)

        def progress(stage, status, data):
            print(f"[{stage}] {status}: {data.get('summary', '')[:50]}...")

        result = await run_market_analysis_ai(
            "分析比亚迪在30万纯电市场的竞争策略",
            progress_callback=progress
        )

        print("\n" + "=" * 60)
        print("Execution Result")
        print("=" * 60)
        print(f"Success: {result.get('success')}")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
        print(f"Skills Used: {result.get('metadata', {}).get('skills_used', [])}")

        if result.get("report"):
            print("\nReport preview:")
            print(result["report"].get("markdown", "")[:500])

    asyncio.run(test())
