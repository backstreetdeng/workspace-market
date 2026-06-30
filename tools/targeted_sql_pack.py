# -*- coding: utf-8 -*-
"""Targeted structured SQL pack with callback support for data-agent."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import sys as _sys
from pathlib import Path as _Path

_agent_root = _Path(__file__).parent.parent
if str(_agent_root) not in _sys.path:
    _sys.path.insert(0, str(_agent_root))

from evidence.evidence_ledger import Evidence

RAG_ENGINE_ROOT = Path(r"E:\AI\data\envs\car_agent_env\ai-decision\rag-engine")
if str(RAG_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_ROOT))

EXPECTED_PYTHON = Path(r"E:\AI\data\envs\car_agent_env\Scripts\python.exe")
CALLBACK_CLIENT_PATH = Path(r"C:\Users\11489\.openclaw\workspace-market\fastapi_18003_adapter\callback_client.py")
CALLBACK_URL = "http://127.0.0.1:18003/callback"

def _emit_callback(session_id: str, phase: str, status: str, summary: str, agent: str = "data-agent") -> None:
    if not session_id:
        return
    cmd = [
        str(EXPECTED_PYTHON),
        str(CALLBACK_CLIENT_PATH),
        "--session-id", session_id,
        "--callback-url", CALLBACK_URL,
        "--phase", phase,
        "--status", status,
        "--agent", agent,
        "--summary", summary,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception:
        pass

def _assert_correct_python() -> None:
    current = Path(sys.executable)
    if current.resolve() == EXPECTED_PYTHON.resolve():
        return
    raise RuntimeError(f"Wrong Python: {current} expected {EXPECTED_PYTHON}")

REQUIRED_TARGETED_SQL_BLOCKS = [
    "market_overview", "monthly_trend", "yoy_change", "competitor_share",
    "target_brand_performance", "model_contribution", "power_mix", "price_and_config",
]

BLOCK_PURPOSES = {
    "market_overview": "TAM/SAM market base and data period",
    "monthly_trend": "monthly trend and MoM volatility",
    "yoy_change": "year-on-year comparison",
    "competitor_share": "competitor share and concentration",
    "target_brand_performance": "target brand SOM and sales base",
    "model_contribution": "target brand model contribution",
    "power_mix": "target brand powertrain mix",
    "price_and_config": "target brand price band and configuration",
}

BLOCK_METRICS = {
    "market_overview": ["sales", "amount", "time_range", "model"],
    "monthly_trend": ["sales", "trend", "mom", "time_range"],
    "yoy_change": ["sales", "yoy", "growth", "time_range"],
    "competitor_share": ["sales", "amount", "competitor", "model"],
    "target_brand_performance": ["sales", "amount", "model", "time_range"],
    "model_contribution": ["sales", "model", "power", "segment"],
    "power_mix": ["sales", "power", "model"],
    "price_and_config": ["price", "price_band", "power", "model"],
}

def run_targeted_sql_pack(
    analysis_plan: Any,
    connection_factory: Optional[Callable[[], Any]] = None,
    session_id: Optional[str] = None,
    callback_url: Optional[str] = None,
) -> Dict[str, Any]:
    plan = _plan_to_dict(analysis_plan)
    
    if session_id:
        _emit_callback(session_id, "DataRunning", "running", "data-agent retrieving data")
    
    conn = None
    cur = None
    try:
        conn = connection_factory() if connection_factory else _db_connect()
        cur = conn.cursor()
        
        if plan.get("target_brand") and not plan.get("brand_aliases"):
            plan["brand_aliases"] = _normalize_brand_aliases(plan["target_brand"], cur)
        
        cur.execute("SELECT MAX(sales_month) AS max_month FROM sales_import")
        max_row = cur.fetchone() or {}
        max_month = int(max_row["max_month"])
        min_month, max_month, prev_min_month, prev_max_month = _period_from_time_range(max_month, str(plan.get("time_range") or ""))
        
        common_cond, common_params = _market_condition(plan)
        brand_cond, brand_params = _brand_condition(plan.get("brand_aliases") or [])
        period_cond = "sales_month BETWEEN %s AND %s"
        period_params = [min_month, max_month]
        prev_period_params = [prev_min_month, prev_max_month]
        
        blocks = []
        
        def add_block(name: str, sql: str, params: List[Any]) -> None:
            cur.execute(sql, params)
            rows = [_jsonable(dict(row)) for row in cur.fetchall()]
            blocks.append({"name": name, "purpose": BLOCK_PURPOSES.get(name, name), "rows": rows, "row_count": len(rows)})
            if session_id:
                msg = "SQL query done, %s fetched %d rows" % (name, len(rows))
                _emit_callback(session_id, "DataRunning", "running", msg)
        
        where_market = period_cond + " AND " + common_cond
        params_market = period_params + common_params
        
        add_block("market_overview", "SELECT SUM(sales) AS total_sales, COUNT(DISTINCT company_name) AS brand_count, COUNT(DISTINCT model_name) AS model_count, MIN(sales_month) AS period_start, MAX(sales_month) AS period_end FROM sales_import WHERE " + where_market, params_market)
        
        add_block("monthly_trend", "SELECT sales_month AS month, SUM(sales) AS sales FROM sales_import WHERE " + where_market + " GROUP BY sales_month ORDER BY sales_month", params_market)
        
        add_block("yoy_change", "SELECT period, SUM(sales) AS sales FROM (SELECT 'current' AS period, sales FROM sales_import WHERE " + where_market + " UNION ALL SELECT 'previous_year' AS period, sales FROM sales_import WHERE " + period_cond + " AND " + common_cond + ") t GROUP BY period", params_market + prev_period_params + common_params)
        
        add_block("competitor_share", "SELECT company_name AS brand, SUM(sales) AS sales, COUNT(DISTINCT model_name) AS model_count, ROUND(SUM(sales) * 100.0 / NULLIF(SUM(SUM(sales))) OVER (), 0), 2) AS share_pct FROM sales_import WHERE " + where_market + " GROUP BY company_name ORDER BY sales DESC LIMIT 12", params_market)
        
        if plan.get("target_brand"):
            where_brand = period_cond + " AND " + common_cond + " AND " + brand_cond
            params_brand = period_params + common_params + brand_params
            add_block("target_brand_performance", "SELECT company_name AS brand, SUM(sales) AS sales, COUNT(DISTINCT model_name) AS model_count, MIN(sales_month) AS period_start, MAX(sales_month) AS period_end FROM sales_import WHERE " + where_brand + " GROUP BY company_name ORDER BY sales DESC LIMIT 10", params_brand)
            add_block("model_contribution", "SELECT model_name AS model, company_name AS brand, tech_type AS power_type, vehicle_level, segment, SUM(sales) AS sales FROM sales_import WHERE " + where_brand + " GROUP BY model_name, company_name, tech_type, vehicle_level, segment ORDER BY sales DESC LIMIT 12", params_brand)
            add_block("power_mix", "SELECT tech_type AS power_type, SUM(sales) AS sales, COUNT(DISTINCT model_name) AS model_count FROM sales_import WHERE " + where_brand + " GROUP BY tech_type ORDER BY sales DESC", params_brand)
            config_where, config_params = _config_condition(plan, cur)
            add_block("price_and_config", "SELECT model_name AS model, maker, energy_type, level, guide_price, price_band, cltc_range, motor_power FROM config_data WHERE " + config_where + " LIMIT 12", config_params)
        
        for block in blocks:
            if block["name"] == "monthly_trend":
                _add_mom(block["rows"])
            if block["name"] == "yoy_change":
                _add_yoy(block["rows"])
        
        if session_id:
            total_rows = sum(b["row_count"] for b in blocks)
            msg = "SQL queries complete, total %d rows" % total_rows
            _emit_callback(session_id, "DataRunning", "running", msg)
        
        return {
            "success": True,
            "query_mode": "targeted_sql_pack",
            "period_start": min_month,
            "period_end": max_month,
            "previous_period_start": prev_min_month,
            "previous_period_end": prev_max_month,
            "blocks": blocks,
            "results": _flatten_blocks(blocks),
        }
    except Exception as exc:
        return {
            "success": False,
            "query_mode": "targeted_sql_pack",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "current_python": sys.executable,
            "expected_python": str(EXPECTED_PYTHON),
            "blocks": [],
            "results": [],
        }
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def build_targeted_sql_evidences(result: Dict[str, Any], analysis_plan: Any) -> List[Evidence]:
    plan = _plan_to_dict(analysis_plan)
    if not result.get("success"):
        return [Evidence(
            source="nl2sql-pg", tool="targeted_sql_pack",
            claim="targeted_sql_pack failed",
            content=str(result.get("error") or "unknown error"),
            time_range=str(plan.get("time_range") or "unknown"),
            metrics=["sales", "amount", "trend", "model", "price", "power", "yoy"],
            data_caliber="PostgreSQL targeted_sql_pack failed",
            source_grade="high", source_credibility=0.20,
            coverage_dimensions=["structured_query_package"],
            coverage_score=0.05, confidence=0.15,
            limitations=[str(result.get("error") or "targeted_sql_pack failed")],
        )]
    evidences = []
    blocks = result.get("blocks") or []
    p_start = result.get("period_start")
    p_end = result.get("period_end")
    period = str(p_start) + " - " + str(p_end)
    for block in blocks:
        name = block.get("name") or "unknown_block"
        rows = block.get("rows") or []
        metrics = BLOCK_METRICS.get(name, ["sales", "amount"])
        sample = json.dumps(rows[:5], ensure_ascii=False, default=str)
        row_count = int(block.get("row_count") or len(rows))
        coverage = _block_coverage_score(name, row_count)
        confidence = round(min(0.92, 0.55 + coverage * 0.35), 3)
        purpose = block.get("purpose") or name
        evidences.append(Evidence(
            source="nl2sql-pg", tool="targeted_sql_pack",
            claim="targeted_sql_pack/" + name + ": " + purpose,
            content="block=" + name + "; row_count=" + str(row_count) + "; sample=" + sample,
            time_range=str(plan.get("time_range") or period),
            metrics=metrics,
            data_caliber="PostgreSQL vectordb.sales_import targeted_sql_pack; period=" + period,
            source_grade="high", source_credibility=0.88,
            coverage_dimensions=metrics + ["time_range", "model"],
            coverage_score=coverage, confidence=confidence,
            limitations=[] if row_count else [name + " returned 0 rows"],
        ))
    return evidences

def missing_required_blocks(result: Optional[Dict[str, Any]], target_brand: Optional[str] = None) -> List[str]:
    required = list(REQUIRED_TARGETED_SQL_BLOCKS)
    if not target_brand:
        required = [b for b in required if b not in {"target_brand_performance", "model_contribution", "power_mix", "price_and_config"}]
    seen = {block.get("name") for block in (result or {}).get("blocks", []) or [] if int(block.get("row_count") or 0) > 0}
    return [block for block in required if block not in seen]

def _normalize_brand_aliases(target_brand: str, cur: Any) -> List[str]:
    import difflib
    cur.execute("SELECT DISTINCT company_name FROM sales_import ORDER BY company_name")
    all_names = [str(row["company_name"]) for row in cur.fetchall()]
    if not all_names:
        return [target_brand]
    primary = target_brand.strip()
    matched = []
    for name in all_names:
        if primary in name or name in primary:
            if name not in matched:
                matched.append(name)
    fuzzy = difflib.get_close_matches(primary, all_names, n=10, cutoff=0.75)
    for name in fuzzy:
        if name not in matched:
            matched.append(name)
    if not matched:
        ratios = [(name, difflib.SequenceMatcher(None, primary, name).ratio()) for name in all_names]
        ratios.sort(key=lambda x: x[1], reverse=True)
        for name, score in ratios[:3]:
            if score > 0.5 and name not in matched:
                matched.append(name)
    if not matched:
        matched = [primary]
    seen = set()
    result_list = []
    for name in matched:
        if name not in seen:
            seen.add(name)
            result_list.append(name)
    return result_list

def _db_connect():
    _assert_correct_python()
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from retrieval.vector_store import DB_CONFIG
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor, connect_timeout=5)

def _plan_to_dict(plan: Any) -> Dict[str, Any]:
    if plan is None:
        return {}
    if isinstance(plan, dict):
        return dict(plan)
    if is_dataclass(plan):
        return asdict(plan)
    if hasattr(plan, "to_dict"):
        return plan.to_dict()
    return dict(getattr(plan, "__dict__", {}) or {})

def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value

def _month_count_from_range(time_range: str) -> int:
    text = time_range or ""
    if _explicit_year(text):
        return 12
    if any(token in text for token in ["near 6 months", "last 6 months", "6 months"]):
        return 6
    if any(token in text for token in ["near 3 months", "last 3 months", "3 months"]):
        return 3
    return 6

def _period_from_time_range(max_month: int, time_range: str) -> Tuple[int, int, int, int]:
    explicit_year = _explicit_year(time_range)
    if explicit_year:
        year_start = explicit_year * 100 + 1
        year_end = explicit_year * 100 + 12
        period_end = min(max_month, year_end)
        if period_end < year_start:
            period_end = year_end
        period_start = year_start
        prev_start = (explicit_year - 1) * 100 + 1
        prev_end = _month_shift(period_end, -12)
        return period_start, period_end, prev_start, prev_end
    month_count = _month_count_from_range(time_range)
    period_start = _month_shift(max_month, -(month_count - 1))
    prev_start = _month_shift(period_start, -month_count)
    prev_end = _month_shift(max_month, -month_count)
    return period_start, max_month, prev_start, prev_end

def _explicit_year(text: str) -> Optional[int]:
    import re
    match = re.search(r"(20\d{2})", text or "")
    if not match:
        return None
    return int(match.group(1))

def _month_shift(yyyymm: int, delta: int) -> int:
    year = yyyymm // 100
    month = yyyymm % 100
    total = year * 12 + (month - 1) + delta
    return (total // 12) * 100 + (total % 12 + 1)

def _market_condition(plan: Dict[str, Any]) -> Tuple[str, List[Any]]:
    parts = []
    params = []
    market_scope = str(plan.get("market_scope") or "")
    power_type = str(plan.get("power_type") or "")
    if power_type == "BEV" or "BEV" in market_scope or "EV" in market_scope:
        parts.append("tech_type IN (%s,%s,%s)")
        params.extend(["BEV", "PHEV", "EREV"])
    elif power_type:
        parts.append("tech_type = %s")
        params.append(power_type)
    if "SUV" in market_scope.upper():
        parts.append("segment ILIKE %s")
        params.append("%SUV%")
    if not parts:
        return "1=1", []
    return " AND ".join(parts), params

def _brand_condition(aliases: List[str]) -> Tuple[str, List[Any]]:
    if not aliases:
        return "1=1", []
    fields = ["company_name", "brand_name", "model_name"]
    parts = []
    params = []
    for alias in aliases:
        for field in fields:
            parts.append(field + " ILIKE %s")
            params.append("%" + alias + "%")
    return "(" + " OR ".join(parts) + ")", params

def _config_condition(plan: Dict[str, Any], cur: Any) -> Tuple[str, List[Any]]:
    import difflib
    aliases = plan.get("brand_aliases") or []
    if not aliases:
        return "1=1", []
    cur.execute("SELECT DISTINCT maker FROM config_data WHERE maker IS NOT NULL ORDER BY maker")
    all_makers = [str(row["maker"]) for row in cur.fetchall()]
    resolved_makers = []
    for alias in aliases:
        found = [m for m in all_makers if alias in m or m in alias]
        if found:
            for m in found:
                if m not in resolved_makers:
                    resolved_makers.append(m)
            continue
        fuzzy = difflib.get_close_matches(alias, all_makers, n=3, cutoff=0.6)
        for m in fuzzy:
            if m not in resolved_makers:
                resolved_makers.append(m)
        if alias not in resolved_makers and alias in all_makers:
            resolved_makers.append(alias)
    if not resolved_makers:
        return "1=1", []
    fields = ["maker", "model_name", "type_name"]
    parts = []
    params = []
    for maker in resolved_makers:
        for field in fields:
            parts.append(field + " ILIKE %s")
            params.append("%" + maker + "%")
    maker_count = len(resolved_makers)
    base_filter = " OR ".join(parts[:maker_count * len(fields)])
    extra_filter = ""
    if plan.get("price_band"):
        extra_filter += " AND price_band ILIKE %s"
        params.append("%" + plan["price_band"] + "%")
    if plan.get("power_type") and plan.get("power_type") != "BEV":
        extra_filter += " AND energy_type ILIKE %s"
        params.append("%" + plan["power_type"] + "%")
    return "(" + base_filter + ")" + extra_filter, params

def _add_mom(rows: List[Dict[str, Any]]) -> None:
    previous = None
    for row in rows:
        sales = row.get("sales") or 0
        row["mom_pct"] = round((sales - previous) * 100.0 / previous, 2) if previous else None
        previous = sales

def _add_yoy(rows: List[Dict[str, Any]]) -> None:
    current = next((row for row in rows if row.get("period") == "current"), None)
    previous = next((row for row in rows if row.get("period") == "previous_year"), None)
    if current and previous and previous.get("sales"):
        current["yoy_pct"] = round((current.get("sales", 0) - previous["sales"]) * 100.0 / previous["sales"], 2)

def _flatten_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for block in blocks:
        for row in block.get("rows") or []:
            item = dict(row)
            item["_block"] = block.get("name")
            item["_purpose"] = block.get("purpose")
            rows.append(item)
    return rows

def _block_coverage_score(block_name: str, row_count: int) -> float:
    base = {"market_overview": 0.78, "monthly_trend": 0.82, "yoy_change": 0.80, "competitor_share": 0.86, "target_brand_performance": 0.82, "model_contribution": 0.84, "power_mix": 0.78, "price_and_config": 0.72}.get(block_name, 0.60)
    if row_count <= 0:
        return 0.20
    if row_count < 3:
        return round(max(0.45, base - 0.15), 3)
    return base
