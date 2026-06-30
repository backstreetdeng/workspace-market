# -*- coding: utf-8 -*-
"""Adapters that expose local specialist agent folders as callable tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

try:
    from evidence.evidence_ledger import Evidence
except ImportError:  # pragma: no cover - package import path variant
    from ..evidence.evidence_ledger import Evidence


def run_specialist_agent(
    *,
    agent_id: str,
    param: str,
    task: Any,
    state: Any,
    workspace_root: Path,
    evidence_report: Dict[str, Any],
) -> Dict[str, Any]:
    if agent_id == "competitor-analyst":
        return _competitor_agent(param, task, state, workspace_root, evidence_report)
    if agent_id == "cost-analyst":
        return _cost_agent(param, task, state, workspace_root, evidence_report)
    if agent_id == "report-generator":
        return _report_agent(param, task, state, workspace_root, evidence_report)
    raise ValueError(f"Unknown specialist agent: {agent_id}")


def _competitor_agent(param: str, task: Any, state: Any, workspace_root: Path, report: Dict[str, Any]) -> Dict[str, Any]:
    plan = getattr(state, "analysis_plan", None)
    plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else {}
    evidence_counts = report.get("by_source") or {}
    competitor_rows = _extract_rows_from_tool_results(state, "competitor_share")
    top_names = [str(row.get("brand") or row.get("maker") or row.get("model")) for row in competitor_rows[:5]]
    content = (
        "竞品分析Agent执行："
        f"target={plan_dict.get('target_brand') or plan_dict.get('market_scope')}; "
        f"param={param}; top_competitors={', '.join(name for name in top_names if name)}; "
        f"evidence_counts={evidence_counts}"
    )
    evidence = Evidence(
        source="analysis-agent",
        tool="competitor-analyst",
        claim="竞品分析Agent完成竞争格局与对标判断",
        content=content,
        time_range=plan_dict.get("time_range", "unknown"),
        metrics=["竞品份额", "竞争梯队", "对标定位"],
        data_caliber="competitor-analyst skill；基于targeted_sql_pack与已入账证据的专业分析",
        source_url=str(workspace_root / "agents" / "competitor-analyst" / "skill.md"),
        source_grade="specialist-agent",
        source_credibility=0.66,
        coverage_dimensions=["竞品矩阵", "波特五力", "4P对比"],
        coverage_score=0.72 if competitor_rows else 0.48,
        confidence=0.70 if competitor_rows else 0.55,
        limitations=[] if competitor_rows else ["未取得competitor_share结构化数据，竞品判断仅为低置信度框架推断"],
    )
    return {
        "agent_id": "competitor-analyst",
        "mode": "tool_adapter",
        "competitor_rows": competitor_rows[:10],
        "evidence": evidence,
    }


def _cost_agent(param: str, task: Any, state: Any, workspace_root: Path, report: Dict[str, Any]) -> Dict[str, Any]:
    plan = getattr(state, "analysis_plan", None)
    plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else {}
    price_rows = _extract_rows_from_tool_results(state, "price_and_config")
    content = (
        "成本测算Agent执行："
        f"target={plan_dict.get('target_brand') or plan_dict.get('market_scope')}; "
        f"price_band={plan_dict.get('price_band')}; power_type={plan_dict.get('power_type')}; "
        f"price_rows={len(price_rows)}; param={param}"
    )
    evidence = Evidence(
        source="analysis-agent",
        tool="cost-analyst",
        claim="成本测算Agent完成成本/定价/规模效应初步判断",
        content=content,
        time_range=plan_dict.get("time_range", "unknown"),
        metrics=["价格带", "动力类型", "规模效应", "成本假设"],
        data_caliber="cost-analyst skill；基于价格配置块与公开证据的成本/定价推断",
        source_url=str(workspace_root / "agents" / "cost-analyst" / "skill.md"),
        source_grade="specialist-agent",
        source_credibility=0.58,
        coverage_dimensions=["成本结构", "定价策略", "规模效应"],
        coverage_score=0.62 if price_rows else 0.42,
        confidence=0.62 if price_rows else 0.48,
        limitations=["缺少供应商报价/BOM明细，成本结论不可作为财务测算定稿"],
    )
    return {
        "agent_id": "cost-analyst",
        "mode": "tool_adapter",
        "price_rows": price_rows[:10],
        "evidence": evidence,
    }


def _report_agent(param: str, task: Any, state: Any, workspace_root: Path, report: Dict[str, Any]) -> Dict[str, Any]:
    plan = getattr(state, "analysis_plan", None)
    plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else {}
    confidence = (report.get("summary") or {}).get("overall_confidence", 0)
    evidence_counts = report.get("by_source") or {}
    content = (
        "报告生成Agent执行："
        f"target={plan_dict.get('target_brand') or plan_dict.get('market_scope')}; "
        f"confidence={confidence:.2f}; evidence_counts={evidence_counts}; param={param}"
    )
    evidence = Evidence(
        source="analysis-agent",
        tool="report-generator-agent",
        claim="报告生成Agent完成报告结构与交付质量检查",
        content=content,
        time_range=plan_dict.get("time_range", "unknown"),
        metrics=["报告结构", "证据引用", "置信度", "下一步行动"],
        data_caliber="report-generator agent；基于EvidenceLedger与七步法报告的交付检查",
        source_url=str(workspace_root / "agents" / "report-generator" / "skill.md"),
        source_grade="specialist-agent",
        source_credibility=0.60,
        coverage_dimensions=["执行摘要", "市场现状", "竞争格局", "机会风险", "战略建议"],
        coverage_score=0.65,
        confidence=max(0.50, min(0.75, float(confidence or 0) * 0.85 + 0.10)),
        limitations=["报告Agent只检查结构和证据引用，不新增事实数据"],
    )
    return {
        "agent_id": "report-generator",
        "mode": "tool_adapter",
        "evidence_counts": evidence_counts,
        "evidence": evidence,
    }


def _extract_rows_from_tool_results(state: Any, block_name: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for tool_result in getattr(state, "tool_results", []) or []:
        result = getattr(tool_result, "result", None)
        if not isinstance(result, dict):
            continue
        for block in result.get("blocks", []) or []:
            if block.get("name") == block_name:
                rows.extend([row for row in block.get("rows", []) or [] if isinstance(row, dict)])
    return rows
