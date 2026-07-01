# -*- coding: utf-8 -*-
"""Pydantic models for the 18003 web chat adapter."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, validator

# 2026-07-01 老大确认: 对齐 TOOLS.md 任务路由表枚举
# - 旧值 (chat.html 历史选项): competitor / policy / opportunity / market / comprehensive / business_analysis
# - 新值 (TOOLS.md 兼容):     None (auto) / competitor_analysis / policy_impact / opportunity_assessment / market_overview / comprehensive_research / business_analysis
AnalysisType = Literal[
    "auto",                     # chat.html 前端"自动识别"默认值
    "business_analysis",        # 商业模式
    "opportunity_assessment",   # 机会评估
    "comprehensive_research",   # 综合研究
    "policy_impact",            # 政策影响
    "competitor_analysis",      # 竞品分析 (含"竞争格局"语义)
    "market_overview",          # 市场趋势 / 市场总览
]

# 旧值白名单 (用于 chat.html 旧版本客户端在过渡期不报错, 仅在 warning 模式接收)
DEPRECATED_ANALYSIS_TYPES = {
    "competitor":   "competitor_analysis",
    "policy":       "policy_impact",
    "opportunity":  "opportunity_assessment",
    "market":       "market_overview",
    "comprehensive": "comprehensive_research",
    "":             "auto",  # 空字符串视作 auto
}


class ChatRequest(BaseModel):
    question: str
    session_id: str
    analysis_type: Optional[str] = None
    time_range: Optional[str] = None
    max_cycles: int = 3

    @validator("analysis_type", pre=True)
    def _normalize_analysis_type(cls, v):
        """Pydantic 层: 接收任意字符串, 改写/保留, 不在 /chat 端点抛 422.

        - None / "" -> 保留为 None (由 /chat 端点决定是否写 "auto")
        - 旧枚举 (competitor / market / comprehensive / policy / opportunity) -> 改写为新枚举
        - 其他字符串 -> 原样保留, 由 /chat 端点决定是接受还是返 400
        """
        if v is None or v == "":
            return None
        if v in DEPRECATED_ANALYSIS_TYPES:
            return DEPRECATED_ANALYSIS_TYPES[v]
        return v


class CallbackPayload(BaseModel):
    session_id: str
    event: Dict[str, Any] = Field(default_factory=dict)


class AdapterEvent(BaseModel):
    event: str = "react"
    data: Dict[str, Any] = Field(default_factory=dict)
