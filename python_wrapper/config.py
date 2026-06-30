"""
Python Wrapper 配置模块
"""

import os
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# Skills 目录
SKILLS_DIR = Path(r"C:\Users\11489\.openclaw\workspace-market\skills")

# RAG Engine 路径
RAG_ENGINE_PATH = r"E:\AI\data\envs\car_agent_env\ai-decision\rag-engine"

# Canonical Python runtime for all market/RAG tools. Do not use system Python for
# these tools; the RAG stack depends on packages installed in this venv.
CAR_AGENT_PYTHON = r"E:\AI\data\envs\car_agent_env\Scripts\python.exe"

# 数据库配置
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "192.168.3.146"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "vectordb"),
    "user": os.environ.get("DB_USER", "vectordb"),
    "password": os.environ.get("DB_PASSWORD", "vectob123")
}

# Skill 映射
SKILL_MODULES = {
    "intent_classifier": "intent_classifier.skill_main",
    "pg-vector-search": "pg_vector_search.vector_search",
    "nl2sql-pg": "nl2sql.nl2sql",
    "automotive-strategy-analysis": "automotive_strategy_analysis.strategy_analysis",
    "report-generator": "report_generator.report_generator"
}

# 分析框架
ANALYSIS_FRAMEWORKS = {
    "pest": "PEST宏观环境分析",
    "porter": "波特五力竞争分析",
    "swot": "SWOT战略分析",
    "fourp": "4P营销组合分析"
}

# 意图类型
INTENT_TYPES = [
    "时机判断", "趋势分析", "画像分析",
    "竞品分析", "机会识别", "政策解读", "综合分析"
]

# 默认配置
DEFAULT_CONFIG = {
    "vector_top_k": 6,
    "sql_limit": 20,
    "trend_limit": 50,
    "parallel_workers": 4,
    "timeout": 120
}
