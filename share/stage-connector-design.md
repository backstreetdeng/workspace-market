# OpenProse 工作流 Stage 衔接设计文档

> 创建时间: 2026-06-02
> 用途: 记录 Stage 间数据衔接的完整分析与解决方案

---

## 一、Stage 1 输出结构

### intent_result 完整字段

```python
{
    # 核心识别结果
    "intent_type": "竞品分析",          # 7种意图: 时机判断|趋势分析|画像分析|竞品分析|机会识别|政策解读|综合分析
    "confidence": 0.85,                  # 置信度 0-1

    # 关键词提取
    "keywords": ["竞品", "比亚迪", "对比", "纯电", "SUV"],  # 提取的关键词
    "brands_mentioned": ["比亚迪"],      # 品牌列表

    # 分析维度
    "dimensions": {
        "价格区间": "20-30万",
        "车型级别": "SUV",
        "动力类型": "纯电"
    },

    # 辅助信息
    "need_sentiment": true,             # 是否需要舆情分析
    "analysis_depth": "standard",       # 分析深度
    "time_range": "最近12个月",          # 时间范围

    # 便捷访问字段
    "price_range": "20-30万",           # 价格区间
    "vehicle_type": "SUV",              # 车型类型
    "power_type": "纯电"                # 动力类型
}
```

### 意图类型枚举

| intent_type | 含义 | 关键词 | 需要SQL | 需要Vector |
|-------------|------|--------|---------|------------|
| 时机判断 | 购车时机 | 合适吗/值得买/降价 | ✅ | ✅ |
| 趋势分析 | 市场走势 | 趋势/前景/未来 | ✅ | ✅ |
| 画像分析 | 用户特征 | 用户画像/消费者 | ✅ | ❌ |
| 竞品分析 | 产品对比 | 对比/竞品/哪个好 | ✅ | ✅ |
| 机会识别 | 市场机会 | 推荐/性价比/机会 | ✅ | ✅ |
| 政策解读 | 政策影响 | 政策/补贴/购置税 | ✅ | ✅ |
| 综合分析 | 默认分类 | - | ✅ | ✅ |

---

## 二、Stage 间依赖矩阵

```
                    ┌─────────────────────────────────────────────────────┐
                    │                    Stage 1                         │
                    │              intent_classifier                       │
                    │                  输出: intent_result                 │
                    └─────────────────────────────────────────────────────┘
                              │                                   │
              ┌───────────────┴───────────────┐                       │
              ▼                               ▼                       │
    ┌─────────────────┐           ┌─────────────────┐               │
    │   Stage 2a     │           │   Stage 2b     │               │
    │ pg-vector-search│           │   nl2sql-pg    │               │
    │                 │           │                 │               │
    │ 输入:           │           │ 输入:           │               │
    │ - vector_query  │           │ - sql_question │               │
    │ - brand_filter  │           │ - conditions   │               │
    │ - metadata      │           │ - query_type   │               │
    └────────┬────────┘           └────────┬────────┘               │
             │                             │                         │
             └─────────────┬───────────────┘                         │
                           ▼                                          │
                 ┌─────────────────┐                                  │
                 │   Stage 2 输出  │                                  │
                 │ - vector_data  │                                  │
                 │ - sql_data     │                                  │
                 └────────┬────────┘                                  │
                          │                                           │
         ┌────────────────┼────────────────┐                         │
         ▼                ▼                ▼                         │
┌─────────────┐  ┌─────────────────┐  ┌─────────────┐                │
│  Stage 3a   │  │   Stage 3b     │  │  Stage 4   │                │
│    PEST     │  │    Porter      │  │ SWOT + 4P  │                │
│             │  │                 │  │             │                │
│ 输入:       │  │ 输入:           │  │ 输入:       │                │
│ - segment   │  │ - segment      │  │ - brand    │                │
│ - market    │  │ - market_data  │  │ - vector  │                │
│ - vector    │  │ - vector_data  │  │ - sql_data │                │
└─────────────┘  └─────────────────┘  └─────────────┘                │
         │                │                │                         │
         └────────────────┼────────────────┘                         │
                          ▼                                          │
                 ┌─────────────────┐                                │
                 │   Stage 3/4 输出 │                                │
                 │ - pest_data     │                                │
                 │ - porter_data   │                                │
                 │ - swot_data     │                                │
                 │ - fourp_data    │                                │
                 └────────┬────────┘                                │
                          │                                          │
                          ▼                                          │
                 ┌─────────────────┐                                 │
                 │   Stage 5      │                                 │
                 │ report-generator│                                 │
                 │                 │                                 │
                 │ 输入:           │                                 │
                 │ - intent_result│                                 │
                 │ - vector_data  │                                 │
                 │ - sql_data     │                                 │
                 │ - pest_data    │                                 │
                 │ - porter_data  │                                 │
                 │ - swot_data    │                                 │
                 │ - fourp_data   │                                 │
                 └─────────────────┘                                 │
```

---

## 三、各 Stage 衔接详细分析

### 3.1 Stage 1 → Stage 2a/2b 衔接

#### 问题诊断

| 问题 | 描述 | 影响 |
|------|------|------|
| Q1 | keywords 包含噪音词（"分析"、"趋势"等） | 检索结果不精准 |
| Q2 | dimensions 未充分利用 | 价格/车型过滤缺失 |
| Q3 | search_mode 硬编码 | 无法按意图优化 |
| Q4 | SQL条件解析原始问题 | 丢失语义信息 |

#### 解决方案：Stage2Connector

```python
# stage2_connector.py
@dataclass
class Stage2Input:
    """Stage 2 统一输入"""
    # 向量检索
    vector_query: str
    vector_brand_filter: str
    vector_metadata_filter: Dict
    search_mode: str

    # SQL查询
    sql_question: str
    sql_conditions: List[str]
    query_type: str
    limit: int

    # 执行控制
    run_vector: bool
    run_sql: bool

def build_stage2_input(intent_result, original_question=None) -> Stage2Input:
    """智能构建 Stage 2 输入"""
    # ... 完整实现见本文档第五节
```

#### 意图驱动的执行策略

```python
INTENT_STRATEGY = {
    "时机判断": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "market_overview", "limit": 20,
        "reason": "需要市场数据+舆情综合判断"
    },
    "趋势分析": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "sales_trend", "limit": 50,
        "reason": "需要趋势数据+行业洞察"
    },
    "画像分析": {
        "run_vector": False, "search_mode": "hybrid",
        "sql_query_type": "segment_distribution", "limit": 30,
        "reason": "主要需要结构化细分数据"
    },
    "竞品分析": {
        "run_vector": True, "search_mode": "keyword",
        "sql_query_type": "brand_comparison", "limit": 10,
        "reason": "需要精确对比+品牌资料"
    },
    "机会识别": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "sales_by_brand", "limit": 20,
        "reason": "需要市场空白+行业机会"
    },
    "政策解读": {
        "run_vector": True, "search_mode": "keyword",
        "sql_query_type": "market_overview", "limit": 10,
        "reason": "需要精准政策文件"
    },
    "综合分析": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "market_overview", "limit": 20,
        "reason": "全面综合分析"
    }
}
```

---

### 3.2 Stage 2 → Stage 3/4 衔接

#### 问题诊断

| 问题 | 描述 | 影响 |
|------|------|------|
| Q5 | Stage 3/4 未接收 vector_data/sql_data | 分析缺少数据支撑 |
| Q6 | segment 固定为"乘用车" | 无法按细分市场分析 |
| Q7 | brand 参数独立于 intent_result | SWOT/4P 可能无品牌 |

#### 解决方案

```python
# stage3_connector.py
@dataclass
class Stage3Input:
    """Stage 3/4 统一输入"""
    # 分析范围
    segment: str          # 市场细分
    brand: str            # 分析品牌（可选）

    # 数据支撑
    market_data: Dict    # sql_data 提取的市场数据
    context_data: List   # vector_data 提取的上下文

    # 分析控制
    frameworks: List[str]  # ["pest", "porter", "swot", "fourp"]

def build_stage3_input(intent_result, sql_data, vector_data) -> Stage3Input:
    """构建 Stage 3/4 输入"""

    # 1. 确定市场细分
    segment = _infer_segment(intent_result, sql_data)

    # 2. 确定分析品牌
    brand = _infer_brand(intent_result, sql_data)

    # 3. 提取市场数据
    market_data = {
        "brand_ranking": _extract_brand_ranking(sql_data),
        "sales_trend": _extract_sales_trend(sql_data),
        "segment_dist": _extract_segment_dist(sql_data)
    }

    # 4. 提取上下文
    context_data = _extract_context(vector_data)

    # 5. 确定分析框架
    frameworks = _select_frameworks(intent_result, brand)

    return Stage3Input(
        segment=segment,
        brand=brand,
        market_data=market_data,
        context_data=context_data,
        frameworks=frameworks
    )

def _infer_segment(intent_result, sql_data) -> str:
    """推断市场细分"""
    # 1. 优先从 dimensions 推断
    vehicle_type = intent_result.get("vehicle_type")
    if vehicle_type:
        segment_map = {
            "SUV": "SUV市场",
            "轿车": "轿车市场",
            "MPV": "MPV市场",
            "紧凑型": "紧凑型车市场",
            "中型": "中型车市场"
        }
        if vehicle_type in segment_map:
            return segment_map[vehicle_type]

    # 2. 从 SQL 数据推断
    if sql_data.get("results"):
        first_result = sql_data["results"][0]
        if "乘用车细分" in first_result:
            return first_result["乘用车细分"]

    # 3. 默认
    return "乘用车市场"

def _infer_brand(intent_result, sql_data) -> Optional[str]:
    """推断分析品牌"""
    # 1. 优先从 intent_result
    brands = intent_result.get("brands_mentioned", [])
    if brands:
        return brands[0]

    # 2. 从 SQL 数据提取
    if sql_data.get("results"):
        for row in sql_data["results"]:
            if "企业名称" in row:
                return row["企业名称"]

    return None

def _select_frameworks(intent_result, brand) -> List[str]:
    """选择分析框架"""
    intent = intent_result.get("intent_type", "综合分析")

    # 基础框架（总是执行）
    frameworks = ["pest", "porter"]

    # 品牌相关框架（需要品牌）
    if brand:
        # 竞品分析、政策解读 → 优先 SWOT
        if intent in ["竞品分析", "政策解读"]:
            frameworks.append("swot")

        # 机会识别 → 优先 4P
        if intent in ["机会识别", "时机判断"]:
            frameworks.append("fourp")

        # 综合分析 → 全部分析
        if intent == "综合分析":
            frameworks.extend(["swot", "fourp"])

    return frameworks
```

---

### 3.3 Stage 3/4 → Stage 5 衔接

#### 问题诊断

| 问题 | 描述 | 影响 |
|------|------|------|
| Q8 | pest_data/porter_data 可能为空 | 报告部分章节缺失 |
| Q9 | swot_data/fourp_data 条件存在 | 报告结构不一致 |
| Q10 | 各模块输出格式不统一 | 报告组装复杂 |

#### 解决方案

```python
# stage5_connector.py
@dataclass
class ReportInput:
    """Stage 5 报告生成输入"""
    # 用户问题
    question: str
    intent_type: str

    # 数据输入
    intent_result: Dict
    vector_data: List
    sql_data: List

    # 分析结果
    pest_data: Optional[Dict]
    porter_data: Optional[Dict]
    swot_data: Optional[Dict]
    fourp_data: Optional[Dict]

    # 质量标记
    data_quality: Dict  # 各模块数据完整性

def build_report_input(
    intent_result,
    vector_results,
    sql_results,
    analysis_results
) -> ReportInput:
    """构建 Stage 5 输入"""

    # 解包分析结果
    pest_data = _unwrap_data(analysis_results.get("pest"))
    porter_data = _unwrap_data(analysis_results.get("porter"))
    swot_data = _unwrap_data(analysis_results.get("swot"))
    fourp_data = _unwrap_data(analysis_results.get("fourp"))

    # 评估数据质量
    data_quality = {
        "intent": _assess_quality(intent_result),
        "vector": _assess_quality(vector_results),
        "sql": _assess_quality(sql_results),
        "pest": _assess_quality(pest_data),
        "porter": _assess_quality(porter_data),
        "swot": _assess_quality(swot_data),
        "fourp": _assess_quality(fourp_data)
    }

    return ReportInput(
        question=intent_result.get("question", ""),
        intent_type=intent_result.get("intent_type", "综合分析"),
        intent_result=intent_result,
        vector_data=vector_results or [],
        sql_data=sql_results or [],
        pest_data=pest_data,
        porter_data=porter_data,
        swot_data=swot_data,
        fourp_data=fourp_data,
        data_quality=data_quality
    )

def _unwrap_data(data) -> Optional[Dict]:
    """解包 Skill 返回的数据（去除 success/data 包装）"""
    if not data:
        return None
    if isinstance(data, dict):
        if data.get("success"):
            return data.get("data", {})
        return data
    return data

def _assess_quality(data) -> str:
    """评估数据质量"""
    if not data:
        return "missing"
    if isinstance(data, dict):
        if not data.get("success", True):
            return "error"
        if len(data) == 0:
            return "empty"
    if isinstance(data, list) and len(data) == 0:
        return "empty"
    return "good"
```

---

### 3.4 Stage 2 内部并行协调

#### 并行执行策略

```python
async def stage2_parallel_execution(intent_result, original_question):
    """Stage 2 并行执行协调"""

    # 1. 构建输入
    stage2_input = build_stage2_input(intent_result, original_question)

    # 2. 并行执行准备
    tasks = []

    if stage2_input.run_vector:
        tasks.append(("vector", _run_vector_search(stage2_input)))

    if stage2_input.run_sql:
        tasks.append(("sql", _run_sql_query(stage2_input)))

    # 3. 并行执行
    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    # 4. 结果组装
    output = {"vector_data": None, "sql_data": None}

    for i, (name, _) in enumerate(tasks):
        if isinstance(results[i], Exception):
            print(f"{name} 执行失败: {results[i]}")
            output[f"{name}_data"] = {"success": False, "error": str(results[i])}
        else:
            output[f"{name}_data"] = results[i]

    return output

async def _run_vector_search(input: Stage2Input):
    """执行向量检索"""
    from vector_search import vector_search
    return vector_search(
        query=input.vector_query,
        top_k=6,
        brand=input.vector_brand_filter,
        search_mode=input.search_mode
    )

async def _run_sql_query(input: Stage2Input):
    """执行 SQL 查询"""
    from nl2sql import query
    return query(
        question=input.sql_question,
        execute=True
    )
```

---

### 3.5 Stage 3/4 内部并行协调

```python
async def stage3_parallel_execution(stage3_input: Stage3Input):
    """Stage 3/4 并行执行协调"""

    tasks = []

    if "pest" in stage3_input.frameworks:
        tasks.append(("pest", _run_pest(stage3_input)))

    if "porter" in stage3_input.frameworks:
        tasks.append(("porter", _run_porter(stage3_input)))

    if "swot" in stage3_input.frameworks and stage3_input.brand:
        tasks.append(("swot", _run_swot(stage3_input)))

    if "fourp" in stage3_input.frameworks and stage3_input.brand:
        tasks.append(("fourp", _run_fourp(stage3_input)))

    # 并行执行
    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    # 结果组装
    output = {}
    for i, (name, _) in enumerate(tasks):
        if isinstance(results[i], Exception):
            output[name] = {"success": False, "error": str(results[i])}
        else:
            output[name] = results[i]

    return output
```

---

## 四、全流程衔接总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户问题                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 1: intent_classifier.classify(question)                              │
│ 输出: intent_result                                                         │
│                                                                             │
│ 衔接检查点:                                                                 │
│   - intent_type 是否有效                                                     │
│   - brands_mentioned 是否有值                                                │
│   - dimensions 是否完整                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 2: 并行执行                                                          │
│ ┌─────────────────────┐  ┌─────────────────────┐                           │
│ │  Stage2a            │  │  Stage2b            │                           │
│ │  vector_search()    │  │  query()           │                           │
│ │  (条件执行)         │  │  (总是执行)         │                           │
│ └─────────────────────┘  └─────────────────────┘                           │
│                                                                             │
│ 衔接检查点:                                                                 │
│   - 检索是否成功                                                           │
│   - SQL 是否返回数据                                                       │
│   - 数据量是否足够                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 3/4: 并行执行（框架依赖 brand）                                        │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                    │
│ │   PEST   │ │  Porter  │ │   SWOT   │ │   4P     │                    │
│ │ (总是执行)│ │ (总是执行)│ │(brand时) │ │(brand时) │                    │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘                    │
│                                                                             │
│ 衔接检查点:                                                                 │
│   - market_data 是否注入                                                    │
│   - context_data 是否传递                                                   │
│   - segment 是否正确                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 5: report_generator.generate()                                       │
│                                                                             │
│ 输入:                                                                       │
│   - intent_result (用户意图)                                                │
│   - vector_data (参考资料)                                                  │
│   - sql_data (市场数据)                                                     │
│   - pest_data (可能为空)                                                   │
│   - porter_data (可能为空)                                                 │
│   - swot_data (可能为空)                                                    │
│   - fourp_data (可能为空)                                                  │
│                                                                             │
│ 衔接检查点:                                                                 │
│   - 各模块数据质量评估                                                      │
│   - 缺失数据的报告策略                                                      │
│   - 报告结构动态调整                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 五、完整衔接代码

### 5.1 stage_connector.py

```python
"""
Stage 衔接器 - 统一管理 Stage 间数据流转
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import re


# ==================== Stage 2 衔接 ====================

@dataclass
class Stage2Input:
    """Stage 2 向量检索+SQL查询输入"""
    vector_query: str = ""
    vector_brand_filter: str = None
    vector_metadata_filter: Dict = field(default_factory=dict)
    search_mode: str = "hybrid"

    sql_question: str = ""
    sql_conditions: List[str] = field(default_factory=list)
    query_type: str = "market_overview"
    limit: int = 20

    run_vector: bool = True
    run_sql: bool = True


INTENT_TO_STRATEGY = {
    "时机判断": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "market_overview", "limit": 20
    },
    "趋势分析": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "sales_trend", "limit": 50
    },
    "画像分析": {
        "run_vector": False, "search_mode": "hybrid",
        "sql_query_type": "segment_distribution", "limit": 30
    },
    "竞品分析": {
        "run_vector": True, "search_mode": "keyword",
        "sql_query_type": "brand_comparison", "limit": 10
    },
    "机会识别": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "sales_by_brand", "limit": 20
    },
    "政策解读": {
        "run_vector": True, "search_mode": "keyword",
        "sql_query_type": "market_overview", "limit": 10
    },
    "综合分析": {
        "run_vector": True, "search_mode": "hybrid",
        "sql_query_type": "market_overview", "limit": 20
    }
}

NOISE_WORDS = {
    "分析", "研究", "如何", "怎么样", "什么", "哪些",
    "趋势", "走势", "前景", "机会", "竞争", "对比",
    "用户", "政策", "补贴"
}

BRAND_KEYWORDS = {
    "比亚迪", "特斯拉", "蔚来", "小鹏", "理想", "问界",
    "小米", "极氪", "零跑", "哪吒", "长安", "吉利",
    "长城", "奇瑞", "大众", "丰田", "本田", "宝马", "奔驰", "奥迪"
}

TECH_MAPPING = {
    "纯电": "纯电动", "电动车": "纯电动", "EV": "纯电动",
    "插混": "插电式混合动力", "PHEV": "插电式混合动力",
    "增程": "增程式", "混动": "混合动力", "HEV": "混合动力",
    "燃油": "汽油"
}


def build_stage2_input(intent_result: Dict, original_question: str = None) -> Stage2Input:
    """根据 intent_result 构建 Stage 2 输入"""

    intent_type = intent_result.get("intent_type", "综合分析")
    dimensions = intent_result.get("dimensions", {})
    brands = intent_result.get("brands_mentioned", [])
    keywords = intent_result.get("keywords", [])
    original_question = original_question or ""

    strategy = INTENT_TO_STRATEGY.get(intent_type, INTENT_TO_STRATEGY["综合分析"])

    # 1. 构建向量检索查询
    semantic_kw = _filter_keywords(keywords)
    for dim in dimensions.values():
        if dim and dim not in semantic_kw:
            semantic_kw.append(dim)

    vector_query = " ".join(semantic_kw) if semantic_kw else original_question

    # 2. 构建向量检索过滤器
    vector_brand = brands[0] if brands else None
    metadata_filter = {k: v for k, v in dimensions.items() if v}

    # 3. 构建SQL条件
    sql_conditions = []

    if brands:
        sql_conditions.append(f'"企业名称" LIKE \'%{brands[0]}%\'')

    if dimensions.get("动力类型"):
        tech = TECH_MAPPING.get(dimensions["动力类型"])
        if tech:
            sql_conditions.append(f'"技术类型" = \'{tech}\'')

    if dimensions.get("车型级别"):
        segment = dimensions["车型级别"]
        if not segment.endswith("车"):
            segment += "车"
        sql_conditions.append(f'"乘用车细分" = \'{segment}\'')

    if dimensions.get("价格区间"):
        sql_conditions.extend(_parse_price_sql(dimensions["价格区间"]))

    # 4. 构建SQL查询问题
    sql_parts = []
    if brands:
        sql_parts.append(f"{brands[0]}销量")
    if dimensions.get("价格区间"):
        sql_parts.append(dimensions["价格区间"])
    if "趋势" in intent_type:
        sql_parts.append("趋势")
    sql_question = " ".join(sql_parts) if sql_parts else original_question

    return Stage2Input(
        vector_query=vector_query,
        vector_brand_filter=vector_brand,
        vector_metadata_filter=metadata_filter,
        search_mode=strategy["search_mode"],
        sql_question=sql_question,
        sql_conditions=sql_conditions,
        query_type=strategy["sql_query_type"],
        limit=strategy["limit"],
        run_vector=strategy["run_vector"],
        run_sql=True
    )


def _filter_keywords(keywords: List[str]) -> List[str]:
    """过滤噪音词"""
    return [
        kw for kw in keywords
        if kw not in NOISE_WORDS
        and (kw in BRAND_KEYWORDS
             or any(c.isdigit() for c in kw)
             or kw in ["SUV", "轿车", "MPV", "紧凑型", "中型", "纯电", "插混", "增程"])
    ]


def _parse_price_sql(price_str: str) -> List[str]:
    """解析价格区间为SQL条件"""
    conditions = []

    match = re.search(r'(\d+)[到至](\d+)万', price_str)
    if match:
        min_p = int(match.group(1)) * 10000
        max_p = int(match.group(2)) * 10000
        conditions.append(f'"厂商指导价" BETWEEN {min_p} AND {max_p}')
        return conditions

    match = re.search(r'(\d+)万以[下内]', price_str)
    if match:
        conditions.append(f'"厂商指导价" < {int(match.group(1)) * 10000}')
        return conditions

    match = re.search(r'(\d+)万以[上外]', price_str)
    if match:
        conditions.append(f'"厂商指导价" > {int(match.group(1)) * 10000}')
        return conditions

    return conditions


# ==================== Stage 3/4 衔接 ====================

@dataclass
class Stage3Input:
    """Stage 3/4 分析框架输入"""
    segment: str = "乘用车市场"
    brand: Optional[str] = None

    market_data: Dict = field(default_factory=dict)
    context_data: List = field(default_factory=list)

    frameworks: List[str] = field(default_factory=lambda: ["pest", "porter"])


SEGMENT_MAP = {
    "SUV": "SUV市场", "轿车": "轿车市场", "MPV": "MPV市场",
    "紧凑型": "紧凑型车市场", "中型": "中型车市场"
}


def build_stage3_input(
    intent_result: Dict,
    sql_data: Dict,
    vector_data: Dict
) -> Stage3Input:
    """构建 Stage 3/4 输入"""

    dimensions = intent_result.get("dimensions", {})
    brands = intent_result.get("brands_mentioned", [])
    intent_type = intent_result.get("intent_type", "综合分析")

    # 推断市场细分
    segment = "乘用车市场"
    if dimensions.get("车型级别"):
        segment = SEGMENT_MAP.get(dimensions["车型级别"], "乘用车市场")

    # 推断品牌
    brand = None
    if brands:
        brand = brands[0]
    elif sql_data.get("results"):
        for row in sql_data["results"]:
            if "企业名称" in row:
                brand = row["企业名称"]
                break

    # 提取市场数据
    market_data = _extract_market_data(sql_data)

    # 提取上下文
    context_data = _extract_context(vector_data)

    # 选择框架
    frameworks = ["pest", "porter"]
    if brand:
        if intent_type in ["竞品分析", "政策解读", "综合分析"]:
            frameworks.append("swot")
        if intent_type in ["机会识别", "时机判断", "综合分析"]:
            frameworks.append("fourp")

    return Stage3Input(
        segment=segment,
        brand=brand,
        market_data=market_data,
        context_data=context_data,
        frameworks=frameworks
    )


def _extract_market_data(sql_data: Dict) -> Dict:
    """从SQL结果提取市场数据"""
    results = sql_data.get("results", [])
    if not results:
        return {}

    return {
        "brand_ranking": [
            {"brand": r.get("企业名称"), "sales": r.get("sales", 0)}
            for r in results if "企业名称" in r
        ],
        "total_sales": sum(r.get("sales", 0) for r in results if "sales" in r),
        "record_count": len(results)
    }


def _extract_context(vector_data: Dict) -> List[str]:
    """从向量检索结果提取上下文"""
    results = vector_data.get("results", [])
    return [
        r.get("content", "")[:200]
        for r in results
        if r.get("content")
    ][:3]


# ==================== Stage 5 衔接 ====================

@dataclass
class ReportInput:
    """Stage 5 报告生成输入"""
    question: str
    intent_type: str

    intent_result: Dict = field(default_factory=dict)
    vector_data: List = field(default_factory=list)
    sql_data: List = field(default_factory=list)

    pest_data: Optional[Dict] = None
    porter_data: Optional[Dict] = None
    swot_data: Optional[Dict] = None
    fourp_data: Optional[Dict] = None

    data_quality: Dict = field(default_factory=dict)


def build_report_input(
    intent_result: Dict,
    vector_results: Dict,
    sql_results: Dict,
    analysis_results: Dict
) -> ReportInput:
    """构建 Stage 5 输入"""

    def unwrap(data):
        if not data:
            return None
        if isinstance(data, dict) and data.get("success"):
            return data.get("data")
        return data if isinstance(data, dict) else None

    pest_data = unwrap(analysis_results.get("pest"))
    porter_data = unwrap(analysis_results.get("porter"))
    swot_data = unwrap(analysis_results.get("swot"))
    fourp_data = unwrap(analysis_results.get("fourp"))

    data_quality = {
        "intent": _quality(intent_result),
        "vector": _quality(vector_results),
        "sql": _quality(sql_results),
        "pest": _quality(pest_data),
        "porter": _quality(porter_data),
        "swot": _quality(swot_data),
        "fourp": _quality(fourp_data)
    }

    return ReportInput(
        question=intent_result.get("question", ""),
        intent_type=intent_result.get("intent_type", "综合分析"),
        intent_result=intent_result,
        vector_data=vector_results.get("results", []) if vector_results else [],
        sql_data=sql_results.get("results", []) if sql_results else [],
        pest_data=pest_data,
        porter_data=porter_data,
        swot_data=swot_data,
        fourp_data=fourp_data,
        data_quality=data_quality
    )


def _quality(data) -> str:
    """评估数据质量"""
    if not data:
        return "missing"
    if isinstance(data, dict) and not data.get("success", True):
        return "error"
    if isinstance(data, (dict, list)) and len(data) == 0:
        return "empty"
    return "good"
```

---

## 六、OpenProse 工作流文件更新

```prose
# 工作流更新后的衔接方式

# ======================
# 阶段1：意图识别
# ======================
let intent_result = session: market_analyst
  prompt: |
    使用 intent-classifier 工具识别用户问题的意图类型。
    用户问题：{question}

# ======================
# 阶段2：数据检索（使用 Stage2Connector）
# ======================
# 导入衔接模块
let stage2_input = build_stage2_input(intent_result, question)

# 向量检索（条件执行）
let vector_data = if stage2_input.run_vector:
  session: market_analyst
    prompt: |
      使用 pg-vector-search 工具检索向量知识库。
      查询：{stage2_input.vector_query}
      品牌过滤：{stage2_input.vector_brand_filter}
      检索模式：{stage2_input.search_mode}
else:
  null

# SQL查询（总是执行）
let sql_data = session: market_analyst
  prompt: |
    使用 nl2sql-pg 工具执行结构化数据查询。
    查询：{stage2_input.sql_question}
    条件：{stage2_input.sql_conditions}

# ======================
# 阶段3/4：战略分析（使用 Stage3Connector）
# ======================
let stage3_input = build_stage3_input(intent_result, sql_data, vector_data)

# PEST分析
let pest_data = session: market_analyst
  prompt: |
    使用 automotive-strategy-analysis 工具执行PEST分析。
    市场细分：{stage3_input.segment}
    市场数据：{stage3_input.market_data}

# 波特五力
let porter_data = session: market_analyst
  prompt: |
    使用 automotive-strategy-analysis 工具执行波特五力分析。
    市场细分：{stage3_input.segment}
    市场数据：{stage3_input.market_data}

# SWOT（条件执行）
let swot_data = if "swot" in stage3_input.frameworks and stage3_input.brand:
  session: market_analyst
    prompt: |
      使用 automotive-strategy-analysis 工具执行SWOT分析。
      品牌：{stage3_input.brand}
      上下文：{stage3_input.context_data}
else:
  null

# 4P（条件执行）
let fourp_data = if "fourp" in stage3_input.frameworks and stage3_input.brand:
  session: market_analyst
    prompt: |
      使用 automotive-strategy-analysis 工具执行4P分析。
      品牌：{stage3_input.brand}
else:
  null

# ======================
# 阶段5：报告生成（使用 Stage5Connector）
# ======================
let report_input = build_report_input(
  intent_result, vector_data, sql_data,
  {pest: pest_data, porter: porter_data, swot: swot_data, fourp: fourp_data}
)

output analysis_report = session: market_analyst
  prompt: |
    使用 report-generator 工具生成报告。
    问题：{report_input.question}
    意图：{report_input.intent_type}
    数据质量：{report_input.data_quality}
    [所有分析结果...]
```

---

## 七、后续待完善

- [ ] Stage2Connector 单元测试
- [ ] Stage3Connector 单元测试
- [ ] Stage5Connector 单元测试
- [ ] 并行执行性能测试
- [ ] 错误处理与回退策略
- [ ] 数据质量监控

---

*文档版本: v1.0*
*最后更新: 2026-06-02*


---

## 市场战略Agent确认（2026-06-02 23:54）

### 确认项

| 检查点 | 状态 | 说明 |
|--------|------|------|
| Stage 1 → Stage 2 衔接 | ✅ | INTENT_TO_STRATEGY 映射完整 |
| Stage 2 → Stage 3/4 衔接 | ✅ | segment/brand 推断逻辑完整 |
| Stage 3/4 条件执行 | ✅ | frameworks 列表控制 |
| Stage 2 并行执行 | ✅ | asyncio.gather 协调 |
| 数据质量评估 | ✅ | _quality() 方法 |

### 待确认问题

1. **report-generator 接口**：需要确认 ReportInput 与 eport_generator.generate_report() 的参数是否匹配
2. **Stage 3 上下文**：pest/porter 分析是否需要 vector_data 作为背景知识？

### 下一步

- [ ] 确认 report-generator 接口签名
- [ ] 确认 pest/porter 是否需要 vector_data
- [ ] 开始 Python Wrapper 开发
