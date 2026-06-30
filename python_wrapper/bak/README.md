# python_wrapper/bak 说明

这里存放已经不再作为当前核心入口使用的旧 Python 代码和重复服务。

当前保留的核心入口是：
- `../workflow_ai_orchestrator.py`
- `../sse_server.py`
- `../skill_caller.py`
- `../upload_server.py`
- `../document_processor.py`

本目录文件用途：
- `workflow.py`：旧固定流程主控脚本，已不再作为核心工作流。
- `stage_connectors.py`：旧固定流程的数据衔接器。
- `upload_service.py`：与 `upload_server.py` 重叠的旧上传服务。
- `sse_server.log`：旧运行日志。

原则：
- 不从这里导入生产入口。
- 需要恢复时，先检查当前架构地图：`../../memory/WORKSPACE_ARCHITECTURE_MAP.md`。
