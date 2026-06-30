# -*- coding: utf-8 -*-
"""Pydantic models for the 18003 web chat adapter."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str
    session_id: str
    analysis_type: Optional[str] = None
    time_range: Optional[str] = None
    max_cycles: int = 3


class CallbackPayload(BaseModel):
    session_id: str
    event: Dict[str, Any] = Field(default_factory=dict)


class AdapterEvent(BaseModel):
    event: str = "react"
    data: Dict[str, Any] = Field(default_factory=dict)
