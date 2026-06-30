# Stage4 缺失问题 - 后端修复清单

**问题**：前端 HTML 定义了 5 个 stage，但 SSE 服务端只发了 4 个，漏了 stage4（品牌分析）

**时间**：2026-06-03 11:27
**责任人**：小C（后端）

---

## 一、前端定义的完整 Stage 流程

| Stage | 名称 | 说明 |
|-------|------|------|
| stage1 | 意图识别 | 识别用户查询类型 |
| stage2 | 数据检索 | SQL + 向量检索 |
| stage3 | 战略分析 | PEST/Porter/SWOT/4P 框架分析 |
| **stage4** | **品牌分析** | **当前缺失** |
| stage5 | 报告生成 | 输出 Markdown 报告 |

---

## 二、需要修改的文件

### 文件1：python_wrapper/sse_server.py

**修改点A**：stages 字典（第 85-90 行）补上 stage4

**原代码**：
stages = {
    "stage1": "意图识别",
    "stage2": "数据检索",
    "stage3": "战略分析",
    "stage5": "报告生成"
}

**改为**：
stages = {
    "stage1": "意图识别",
    "stage2": "数据检索",
    "stage3": "战略分析",
    "stage4": "品牌分析",
    "stage5": "报告生成"
}

---

**修改点B**：_generate_summary 函数（约第 192-277 行）补上 stage4 分支

在 elif stage == "stage3": 之后、elif stage == "stage5": 之前加上：

elif stage == "stage4":
    # 品牌分析
    if data and isinstance(data, dict):
        brand = data.get("brand", "未知")
        ranking = data.get("ranking", [])
        if ranking:
            top3 = [r.get("brand", "?") for r in ranking[:3]]
            return f"品牌：{brand} | Top3：{', '.join(top3)}"
        return f"品牌：{brand} | 分析完成"
    return "完成"

---

### 文件2：python_wrapper/workflow.py

**修改点**：在 stage3 done 之后、stage5 running 之前，插入 stage4 进度回调

在以下位置（约第 228-234 行附近）：

原文：
if progress_callback:
    await progress_callback("stage3", "done", {...})
# Stage 5: Report generation
if progress_callback:
    await progress_callback("stage5", "running", None)

改为：
if progress_callback:
    await progress_callback("stage3", "done", {...})

# Stage 4: 品牌分析
if progress_callback:
    await progress_callback("stage4", "running", None)

brand_data = {
    "brand": stage3_input.brand,
    "models": [],
    "ranking": sql_data.get("brand_ranking", []) if sql_data else []
}
if progress_callback:
    await progress_callback("stage4", "done", brand_data)

# Stage 5: Report generation
if progress_callback:
    await progress_callback("stage5", "running", None)

---

## 三、数据来源说明

- stage3_input.brand：通过 build_stage3_input 的 _infer_brand 从意图结果中获取，无需额外查询
- brand_ranking：来自 stage_connectors.py 的 _build_brand_ranking，字段名为 brand

## 四、验证方法

调用 /analyze_sse 接口，检查返回的 progress 事件是否依次包含：
1. stage: "stage4", status: "running"
2. stage: "stage4", status: "done", data 有 brand/ranking 字段