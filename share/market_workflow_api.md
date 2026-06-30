# 市场战略Agent → Python Wrapper 开发共享接口文档
更新时间：2026-06-03 00:14
版本：v2.0

---

## 一、工作流阶段概览（5大阶段）

`
用户问题
    │
    ▼
Stage 1: 意图识别（唯一必须先执行的）
    │→ 输出: intent_result {intent_type, brands_mentioned, keywords, dimensions}
    │
    ├──────────────────────────────┐
    ▼                              ▼
Stage 2a: 向量检索              Stage 2b: SQL查询
    │                              │
    │← intent_result (优化)          │← intent_result (优化)
    ▼                              ▼
Stage 3a: PEST分析 ←───────→ Stage 3b: 波特五力
    │
    ├──────────┬───────────────────┤
    ▼          ▼                   ▼
Stage 4a:    Stage 4b:         (Stage 5)
SWOT分析     4P分析
(条件执行)   (条件执行)
    │          │
    └────┬─────┘
         ▼
    Stage 5: 报告生成
`

---

## 二、各阶段详细依赖（输入/输出/消费关系）

| 阶段 | Skill | 主输入 | 前置输出 | 消费来源 | 条件 |
|------|-------|--------|---------|---------|------|
| **Stage 1** | intent_classifier | question | ❌ | Stage 2,4,5 | 必须 |
| **Stage 2a** | pg-vector-search | question | ✅ intent_result | Stage 5 | 可选 |
| **Stage 2b** | nl2sql-pg | question | ✅ intent_result | Stage 5 | 可选 |
| **Stage 3a** | pest | segment | ❌ | Stage 5 | 可选 |
| **Stage 3b** | porter | segment | ❌ | Stage 5 | 可选 |
| **Stage 4a** | swot | brand | ✅ intent_result | Stage 5 | 条件执行 |
| **Stage 4b** | fourp | brand | ✅ intent_result | Stage 5 | 条件执行 |
| **Stage 5** | report-generator | - | 全部 | ❌ | 必须 |

---

## 三、Stage 1 输出详解（intent_result）

`python
{
    # 意图识别
    "intent_type": "竞品分析",          # 7种意图: 趋势判断|竞品分析|机会识别|产品定义|用户画像|品牌识别|综合分析
    "confidence": 0.85,                  # 置信度 0-1

    # 关键词提取
    "keywords": ["比亚迪", "特斯拉", "SUV", "纯电"],  # 提取的关键词
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

    # 数据分发字段
    "price_range": "20-30万",
    "vehicle_type": "SUV",
    "power_type": "纯电"
}
`

### Stage 1 输出消费关系
| 消费者 | 使用字段 | 用途 |
|--------|---------|------|
| Stage 2a (pg-vector-search) | keywords, brands_mentioned | 检索优化 |
| Stage 2b (nl2sql-pg) | keywords, brands_mentioned | 查询优化 |
| Stage 4a (SWOT) | brands_mentioned[0] | 品牌分析 |
| Stage 4b (4P) | brands_mentioned[0] | 品牌分析 |

---

## 四、无缝衔接方案

### Stage 1 → Stage 2 (已完成：skill 封装)

`python
# Stage 2a: pg-vector-search
def search_by_intent(intent_result, top_k=6):
    keywords = intent_result.get("keywords", [])
    brands = intent_result.get("brands_mentioned", [])
    query = " ".join(keywords) if keywords else intent_result.get("question", "")
    brand = brands[0] if brands else None
    return vector_search(query=query, top_k=top_k, brand=brand)

# Stage 2b: nl2sql-pg
def query_with_intent(intent_result):
    keywords = intent_result.get("keywords", [])
    brands = intent_result.get("brands_mentioned", [])
    # 构建查询...
`

**✅ 已封装，Python Wrapper 直接调用 y_intent() 方法即可**

---

### Stage 1 → Stage 4 (需实现：brand 提取)

`python
# Stage 4 需要从 intent_result 提取 brand
brand = intent_result.get("brands_mentioned", [None])[0]
if brand:
    swot_result = swot_analysis(brand=brand)
    fourp_result = fourp_analysis(brand=brand)
else:
    swot_result, fourp_result = None, None
`

**✅ 简单条件判断，Python Wrapper 直接实现**

---

### Stage 2/3/4 → Stage 5 (需实现：数据汇总)

`python
# Stage 5 接收所有数据
report = report_generator.generate_report(
    question=question,
    intent_type=intent_result.get("intent_type"),
    vector_results=vector_data.get("results", []),
    sql_results=sql_data.get("results", []),
    pest_result=pest_result,
    porter_result=porter_result,
    swot_result=swot_result,
    fourp_result=fourp_result
)
`

**✅ 直接传递，skill 已封装好数据格式**

---

## 五、全流程衔接检查清单

| 衔接点 | 方案 | 状态 |
|--------|------|------|
| Stage 1 → Stage 2a | search_by_intent(intent_result) | ✅ 已封装 |
| Stage 1 → Stage 2b | query_with_intent(intent_result) | ✅ 已封装 |
| Stage 1 → Stage 4a | 提取 rands_mentioned[0] | ✅ Python Wrapper 处理 |
| Stage 1 → Stage 4b | 提取 rands_mentioned[0] | ✅ Python Wrapper 处理 |
| Stage 2 → Stage 5 | 直接传递 esults | ✅ 已封装 |
| Stage 3 → Stage 5 | 直接传递 data | ✅ 已封装 |
| Stage 4 → Stage 5 | 条件传递（无brand时传None） | ✅ Python Wrapper 处理 |

**结论：所有衔接问题都已解决，skill 封装良好，Python Wrapper 只需按顺序调用即可。**

---

## 六、Python Wrapper 执行流程（最终版）

`python
async def run_market_analysis(question: str):
    # 1. Stage 1: 意图识别（必须）
    intent_result = await call_skill("intent_classifier", {"question": question})
    
    # 2. Stage 2: 数据检索（可并行，使用 intent_result 优化）
    vector_task = call_skill_async("pg-vector-search", {
        "action": "by_intent",
        "intent_result": intent_result
    })
    sql_task = call_skill_async("nl2sql-pg", {
        "action": "by_intent",
        "intent_result": intent_result
    })
    vector_data, sql_data = await asyncio.gather(vector_task, sql_task)
    
    # 3. Stage 3: 战略分析（可并行）
    pest_task = call_skill_async("automotive-strategy-analysis", {"action": "pest"})
    porter_task = call_skill_async("automotive-strategy-analysis", {"action": "porter"})
    pest_result, porter_result = await asyncio.gather(pest_task, porter_task)
    
    # 4. Stage 4: 品牌分析（条件执行）
    brand = intent_result.get("brands_mentioned", [None])[0]
    if brand:
        swot_task = call_skill_async("automotive-strategy-analysis", {"action": "swot", "brand": brand})
        fourp_task = call_skill_async("automotive-strategy-analysis", {"action": "fourp", "brand": brand})
        swot_result, fourp_result = await asyncio.gather(swot_task, fourp_task)
    else:
        swot_result, fourp_result = None, None
    
    # 5. Stage 5: 报告生成
    report = report_generator.generate_report(
        question=question,
        intent_type=intent_result.get("intent_type"),
        pest_result=pest_result,
        porter_result=porter_result,
        swot_result=swot_result,
        fourp_result=fourp_result,
        vector_results=vector_data.get("results", []),
        sql_results=sql_data.get("results", [])
    )
    
    return report
`

---

## 七、SSE 事件格式（前端对接用）

`json
{"eventType": "step_begin", "stepId": "intent", "stageName": "阶段1｜意图识别", "status": "running"}
{"eventType": "step_finish", "stepId": "intent", "fullContent": "{...}", "status": "success"}
{"eventType": "step_begin", "stepId": "vector_search", "stageName": "阶段2a｜向量检索", "status": "running"}
{"eventType": "step_finish", "stepId": "vector_search", "status": "success"}
...
{"eventType": "workflow_end", "stepId": "final_report", "status": "success"}
`

---
版本历史：
- v1.0: 2026-06-02 23:45 初始版本
- v2.0: 2026-06-03 00:14 重建文档，更新衔接方案