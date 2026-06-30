# -*- coding: utf-8 -*-
"""
文档上传API服务

提供RESTful API接口：
- POST /upload - 上传文档
- GET /documents - 获取文档列表
- GET /documents/{id} - 获取文档详情
- GET /documents/{id}/content - 获取文档内容（Markdown）
- GET /search - 搜索相似内容
- DELETE /documents/{id} - 删除文档
"""

import os
import sys
import asyncio
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# 添加项目路径
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_PATH)

from document_processor import (
    DocumentUploadService,
    get_document_list,
    get_document_detail,
    search_documents
)


# ==================== 配置 ====================

# 上传目录（支持环境变量配置）
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(PROJECT_PATH, "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls'}


# ==================== Pydantic模型 ====================

class UploadResponse(BaseModel):
    success: bool
    document_id: Optional[int] = None
    file_name: str
    message: str
    chunks_count: int = 0
    error: Optional[str] = None


class DocumentListItem(BaseModel):
    id: int
    file_name: str
    source: str
    brand: str
    category: str
    upload_date: Optional[str]
    chunks_count: int


class SearchResult(BaseModel):
    content: str
    score: float
    document_id: int
    chunk_index: int
    file_name: Optional[str] = None
    brand: Optional[str] = None


# ==================== FastAPI应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    print(f"Document Upload Server started")
    print(f"Upload directory: {UPLOAD_DIR}")
    yield
    print("Document Upload Server stopped")


app = FastAPI(
    title="文档上传服务",
    description="文档上传、解析、向量化和检索服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API接口 ====================

@app.get("/")
async def root():
    """服务信息"""
    return {
        "name": "文档上传服务",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload",
            "documents": "GET /documents",
            "document_detail": "GET /documents/{id}",
            "document_content": "GET /documents/{id}/content",
            "search": "GET /search",
            "delete": "DELETE /documents/{id}"
        }
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form(None),
    brand: str = Form(None),
    category: str = Form(None),
    car_model: str = Form(None),
    publish_date: str = Form(None)
):
    """
    上传文档

    支持格式: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS

    Args:
        file: 上传的文件
        source: 来源（可选）
        brand: 品牌（可选）
        category: 分类（可选）
        car_model: 车型（可选）
        publish_date: 发布日期（可选，格式：YYYY-MM-DD）

    Returns:
        UploadResponse: 上传结果
    """
    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return UploadResponse(
            success=False,
            file_name=file.filename,
            error=f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 保存上传的文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 处理上传
        service = DocumentUploadService(upload_dir=UPLOAD_DIR)
        result = service.upload(
            file_path=tmp_path,
            source=source,
            brand=brand,
            category=category,
            car_model=car_model,
            publish_date=publish_date
        )

        return UploadResponse(
            success=result.success,
            document_id=result.document_id,
            file_name=result.file_name,
            message=result.message,
            chunks_count=result.chunks_count,
            error=result.error
        )

    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/documents", response_model=List[DocumentListItem])
async def list_documents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    获取文档列表

    Args:
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        文档列表
    """
    docs = get_document_list(limit=limit, offset=offset)
    return docs


@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    """
    获取文档详情

    Args:
        doc_id: 文档ID

    Returns:
        文档详情，包含切片列表
    """
    doc = get_document_detail(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/documents/{doc_id}/content")
async def get_document_content(doc_id: int):
    """
    获取文档内容（Markdown格式）

    Args:
        doc_id: 文档ID

    Returns:
        Markdown文本
    """
    doc = get_document_detail(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 合并所有chunks为完整Markdown
    chunks = doc.get("chunks", [])
    if not chunks:
        return {"success": True, "content": "", "doc_id": doc_id}

    # 按顺序拼接
    markdown_parts = []
    for chunk in sorted(chunks, key=lambda x: x.get("chunk_index", 0)):
        content = chunk.get("content", "")
        if content:
            markdown_parts.append(content)

    full_content = "\n\n---\n\n".join(markdown_parts)

    return {
        "success": True,
        "doc_id": doc_id,
        "file_name": doc.get("file_name"),
        "content": full_content,
        "chunks_count": len(chunks)
    }


@app.get("/search", response_model=List[SearchResult])
async def search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    brand: str = Query(None)
):
    """
    搜索相似内容

    Args:
        q: 查询文本
        top_k: 返回数量
        brand: 品牌过滤（可选）

    Returns:
        相似内容列表
    """
    results = search_documents(query=q, top_k=top_k, brand=brand)
    return results


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """
    删除文档

    Args:
        doc_id: 文档ID

    Returns:
        删除结果
    """
    from document_processor import DocumentDB
    db = DocumentDB()

    if not db.get_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")

    success = db.delete_document(doc_id)

    # 删除上传的文件
    if success:
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(f"{doc_id}_"):
                os.remove(os.path.join(UPLOAD_DIR, f))

    return {"success": success, "doc_id": doc_id}


@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    from document_processor import DocumentDB
    db = DocumentDB()

    docs = db.get_documents(limit=1000)
    total_docs = len(docs)
    total_chunks = sum(d.chunks_count for d in docs)

    # 按品牌统计
    brand_stats = {}
    for doc in docs:
        brand = doc.brand or "未分类"
        if brand not in brand_stats:
            brand_stats[brand] = {"docs": 0, "chunks": 0}
        brand_stats[brand]["docs"] += 1
        brand_stats[brand]["chunks"] += doc.chunks_count

    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "by_brand": brand_stats
    }


# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False
    )
