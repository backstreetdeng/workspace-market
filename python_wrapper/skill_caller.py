# -*- coding: utf-8 -*-
"""
Skill Caller Module

Provides unified async interface for skill invocations
"""

import sys
import asyncio
import importlib
import threading
from typing import Dict, Any, Optional
from pathlib import Path

# RAG Engine path
RAG_ENGINE_PATH = r"E:\AI\data\envs\car_agent_env\ai-decision\rag-engine"
if RAG_ENGINE_PATH not in sys.path:
    sys.path.insert(0, RAG_ENGINE_PATH)

# Skills directory
SKILLS_DIR = Path(r"C:\Users\11489\.openclaw\workspace-market\skills")

# Module import lock to prevent parallel import deadlock
_import_lock = threading.Lock()


class SkillCaller:
    """Skill Caller"""
    __slots__ = ('_cache',)

    def __init__(self):
        self._cache = {}

    def _load_skill_module(self, skill_name: str):
        """Dynamically load skill module"""
        if skill_name in self._cache:
            return self._cache[skill_name]

        # Skill directory mapping
        skill_dir_map = {
            "intent_classifier": SKILLS_DIR / "intent-classifier",
            "pg-vector-search": SKILLS_DIR / "pg-vector-search",
            "nl2sql-pg": SKILLS_DIR / "nl2sql-pg",
            "automotive-strategy-analysis": SKILLS_DIR / "automotive-strategy-analysis",
            "report-generator": SKILLS_DIR / "report-generator"
        }

        if skill_name not in skill_dir_map:
            raise ValueError(f"Unknown skill: {skill_name}")

        skill_path = skill_dir_map[skill_name]
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        # Use lock to prevent parallel import deadlock
        with _import_lock:
            # Double-check (thread-safe)
            if skill_name in self._cache:
                return self._cache[skill_name]

            # Load correct module/function for each skill
            # All use skill_main(action, params) interface except report-generator
            if skill_name == "intent_classifier":
                from skill_main import skill_main as func
            elif skill_name == "pg-vector-search":
                # skill_main is inside vector_search.py
                from vector_search import skill_main as func
            elif skill_name == "nl2sql-pg":
                # skill_main is inside nl2sql.py
                from nl2sql import skill_main as func
            elif skill_name == "automotive-strategy-analysis":
                from strategy_analysis import skill_main as func
            elif skill_name == "report-generator":
                from report_generator import generate_report as func
            else:
                raise NotImplementedError(f"Skill {skill_name} loading not implemented")

            self._cache[skill_name] = func
        return func

    async def call(self, skill_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Async call Skill - uses skill_main(action, params) interface"""
        func = self._load_skill_module(skill_name)
        loop = asyncio.get_event_loop()
        
        # Special handling for report-generator which doesn't use action
        if skill_name == "report-generator":
            result = await loop.run_in_executor(
                None,
                lambda: func(**params)
            )
        else:
            # Standard: skill_main(action, params)
            result = await loop.run_in_executor(
                None,
                lambda: func(action, params)
            )
        return result

    async def classify_intent(self, question: str) -> Dict[str, Any]:
        """Intent classification"""
        result = await self.call("intent_classifier", "classify", {"question": question})
        if result.get("success") and "result" in result:
            return result["result"]
        return result

    async def vector_search(
        self,
        query: str,
        top_k: int = 6,
        brand: str = None,
        search_mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """Vector search"""
        return await self.call(
            "pg-vector-search",
            "search",
            {"query": query, "top_k": top_k, "brand": brand, "search_mode": search_mode}
        )

    async def sql_query(self, question: str, execute: bool = True) -> Dict[str, Any]:
        """SQL query"""
        return await self.call(
            "nl2sql-pg",
            "query",
            {"question": question, "execute": execute}
        )

    async def pest_analysis(self, brand: str = None, segment: str = "乘用车", sql_data: Dict = None, vector_data: Dict = None) -> Dict[str, Any]:
        """PEST analysis"""
        return await self.call(
            "automotive-strategy-analysis",
            "pest",
            {"brand": brand, "segment": segment, "sql_data": sql_data, "vector_data": vector_data}
        )

    async def porter_analysis(self, brand: str = None, segment: str = "乘用车", sql_data: Dict = None, vector_data: Dict = None) -> Dict[str, Any]:
        """Porter five forces analysis"""
        return await self.call(
            "automotive-strategy-analysis",
            "porter",
            {"brand": brand, "segment": segment, "sql_data": sql_data, "vector_data": vector_data}
        )

    async def swot_analysis(self, brand: str, segment: str = None, sql_data: Dict = None, vector_data: Dict = None) -> Dict[str, Any]:
        """SWOT analysis"""
        return await self.call(
            "automotive-strategy-analysis",
            "swot",
            {"brand": brand, "segment": segment, "sql_data": sql_data, "vector_data": vector_data}
        )

    async def fourp_analysis(self, brand: str, segment: str = None, sql_data: Dict = None, vector_data: Dict = None) -> Dict[str, Any]:
        """4P analysis"""
        return await self.call(
            "automotive-strategy-analysis",
            "fourp",
            {"brand": brand, "segment": segment, "sql_data": sql_data, "vector_data": vector_data}
        )

    async def brand_analysis(self, brand: str = None, sql_data: Dict = None, vector_data: Dict = None, question: str = None) -> Dict[str, Any]:
        """
        Brand analysis - analyzes brand market position and competitive advantages
        """
        # 调用 automotive-strategy-analysis skill
        # 使用 comprehensive 分析模式
        return await self.call(
            "automotive-strategy-analysis",
            "comprehensive",
            {
                "brand": brand,
                "sql_data": sql_data,
                "vector_data": vector_data,
                "question": question  # 用于从问题中提取品牌
            }
        )

    async def generate_report(
        self,
        question: str,
        intent_type: str,
        pest_result: Dict = None,
        porter_result: Dict = None,
        swot_result: Dict = None,
        fourp_result: Dict = None,
        brand_result: Dict = None,
        vector_results: list = None,
        sql_results: list = None
    ) -> Dict[str, Any]:
        """Generate report - direct method, not via call()"""
        func = self._load_skill_module("report-generator")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: func(
                question=question,
                intent_type=intent_type,
                pest_result=pest_result,
                porter_result=porter_result,
                swot_result=swot_result,
                fourp_result=fourp_result,
                brand_result=brand_result,
                vector_results=vector_results,
                sql_results=sql_results
            )
        )


# Global instance
_caller = None

def get_caller() -> SkillCaller:
    """Get SkillCaller singleton"""
    global _caller
    if _caller is None:
        _caller = SkillCaller()
    return _caller