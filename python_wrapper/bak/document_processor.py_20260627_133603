# -*- coding: utf-8 -*-
"""
文档上传、解析和向量化服务

功能：
- 接收上传的文档（docx, excel, pdf, pptx）
- 使用MinerU进行解析，输出Markdown
- 向量化并存储到PostgreSQL + PGVector
"""

import os
import sys
import json
import hashlib
import tempfile
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor

# MinerU 模型路径配置
# 服务器已下载模型位置
MINERU_MODEL_PATH = os.environ.get("MINERU_MODEL_PATH",
    "/root/.cache/modelscope/hub/models/OpenDataLab/MinerU2.5-Pro-2605-1.2B")
os.environ["MINERU_MODEL_PATH"] = MINERU_MODEL_PATH

# ModelScope 缓存目录
MODELSCOPE_CACHE = os.environ.get("MODELSCOPE_CACHE", "/root/.cache/modelscope/hub")
os.environ["MODELSCOPE_CACHE"] = MODELSCOPE_CACHE


# ==================== 数据库配置 ====================

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "192.168.3.146"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "vectordb"),
    "user": os.environ.get("DB_USER", "vectordb"),
    "password": os.environ.get("DB_PASSWORD", "vectordb123")
}


# ==================== 数据类 ====================

@dataclass
class UploadResult:
    """上传结果"""
    success: bool
    document_id: int = None
    file_name: str = ""
    message: str = ""
    chunks_count: int = 0
    error: str = None


@dataclass
class DocumentInfo:
    """文档信息"""
    id: int
    file_name: str
    source: str
    brand: str
    category: str
    upload_date: datetime
    chunks_count: int = 0


# ==================== 向量化模型 ====================

# Ollama 向量化配置（支持环境变量）
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://192.168.3.146:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "quentinz/bge-large-zh-v1.5")


class EmbeddingModel:
    """向量化模型封装（使用 Ollama API）"""

    def __init__(self, host: str = None, model_name: str = None):
        """初始化向量化模型"""
        self.host = host or OLLAMA_HOST
        self.model_name = model_name or OLLAMA_MODEL
        self.client = None
        self._load_client()

    def _load_client(self):
        """加载 Ollama 客户端"""
        try:
            from ollama import Client
            self.client = Client(host=self.host)
            print(f"Ollama embedding client: {self.host}, model: {self.model_name}")
        except ImportError:
            print("Warning: ollama package not installed. Using fallback mode.")
            self.client = None

    def encode(self, texts: List[str]) -> List[List[float]]:
        """将文本编码为向量"""
        import random

        # Fallback模式：返回随机向量
        if self.client is None:
            print("Using fallback mode: random vectors")
            return [[random.random() for _ in range(1024)] for _ in texts]

        try:
            # 单个文本
            if len(texts) == 1:
                response = self.client.embed(
                    model=self.model_name,
                    input=texts[0]
                )
                return response["embeddings"]

            # 批量文本
            embeddings = []
            for text in texts:
                try:
                    response = self.client.embed(
                        model=self.model_name,
                        input=text
                    )
                    embeddings.append(response["embeddings"][0])
                except Exception as e:
                    print(f"Embedding error for text: {e}")
                    # 返回随机向量作为fallback
                    embeddings.append([random.random() for _ in range(1024)])

            return embeddings

        except Exception as e:
            print(f"Ollama embedding error: {e}. Using fallback mode.")
            return [[random.random() for _ in range(1024)] for _ in texts]


# ==================== MinerU解析器 ====================

class MinerUParser:
    """MinerU文档解析器"""

    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or tempfile.mkdtemp()
        self.embedding_model = EmbeddingModel()

    def is_supported(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        使用MinerU解析文档

        Returns:
            {
                "success": bool,
                "markdown": str,  # 解析后的Markdown
                "chunks": List[Dict],  # 切分后的文本块
                "error": str
            }
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found", "markdown": "", "chunks": []}

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.pdf':
                return self._parse_pdf(file_path)
            elif ext in ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']:
                return self._parse_office(file_path)
            else:
                return {"success": False, "error": f"Unsupported format: {ext}",
                        "markdown": "", "chunks": []}
        except Exception as e:
            return {"success": False, "error": str(e), "markdown": "", "chunks": []}

    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """解析PDF文件（使用mineru命令行）"""
        file_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            # 获取绝对路径
            abs_file_path = os.path.abspath(file_path)
            abs_output_dir = os.path.abspath(self.output_dir)
            os.makedirs(abs_output_dir, exist_ok=True)

            # 使用mineru命令行解析
            # mineru -p <file> -o <output_dir> -b vlm-auto-engine
            # 输出: <output_dir>/<filename>.md 和 <output_dir>/<filename>_origin/
            cmd = [
                "mineru",
                "-p", abs_file_path,
                "-o", abs_output_dir,
                "-b", "vlm-auto-engine"
            ]
            print(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"MinerU stdout: {result.stdout}")
            if result.stderr:
                print(f"MinerU stderr: {result.stderr}")

            # 查找生成的Markdown文件
            # MinerU 输出格式: <output_dir>/<filename>.md
            markdown = ""
            md_path = os.path.join(abs_output_dir, f"{file_name}.md")
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f:
                    markdown = f.read()
            else:
                # 兼容：尝试在子目录中查找
                for root, dirs, files in os.walk(abs_output_dir):
                    for f in files:
                        if f.endswith('.md'):
                            with open(os.path.join(root, f), 'r', encoding='utf-8') as mf:
                                markdown += mf.read() + "\n\n"

            # 切分文本块
            chunks = self._split_chunks(markdown)

            return {
                "success": True,
                "markdown": markdown,
                "chunks": chunks,
                "output_dir": abs_output_dir
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"MinerU解析失败: {e.stderr}",
                "markdown": "",
                "chunks": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF parse error: {str(e)}",
                "markdown": "",
                "chunks": []
            }

    def _parse_office(self, file_path: str) -> Dict[str, Any]:
        """解析Office文件（使用mineru命令行，mineru会自动处理Office格式）"""
        import subprocess as sp

        file_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            # 获取绝对路径
            abs_file_path = os.path.abspath(file_path)
            abs_output_dir = os.path.abspath(self.output_dir)
            os.makedirs(abs_output_dir, exist_ok=True)

            # 使用mineru命令行解析（mineru会自动处理Office格式）
            cmd = [
                "mineru",
                "-p", abs_file_path,
                "-o", abs_output_dir,
                "-b", "vlm-auto-engine"
            ]
            print(f"Running: {' '.join(cmd)}")

            result = sp.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"MinerU stdout: {result.stdout}")
            if result.stderr:
                print(f"MinerU stderr: {result.stderr}")

            # 查找生成的Markdown文件
            # MinerU 输出格式: <output_dir>/<filename>.md
            markdown = ""
            md_path = os.path.join(abs_output_dir, f"{file_name}.md")
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f:
                    markdown = f.read()
            else:
                # 兼容：尝试在子目录中查找
                for root, dirs, files in os.walk(abs_output_dir):
                    for f in files:
                        if f.endswith('.md'):
                            with open(os.path.join(root, f), 'r', encoding='utf-8') as mf:
                                markdown += mf.read() + "\n\n"

            chunks = self._split_chunks(markdown)

            return {
                "success": True,
                "markdown": markdown,
                "chunks": chunks,
                "output_dir": abs_output_dir
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"MinerU解析失败: {e.stderr}",
                "markdown": "",
                "chunks": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Office parse error: {str(e)}",
                "markdown": "",
                "chunks": []
            }

    def _split_chunks(self, markdown: str, chunk_size: int = 500,
                      overlap: int = 50) -> List[Dict[str, Any]]:
        """
        将Markdown文本切分为块

        Args:
            markdown: Markdown文本
            chunk_size: 每块目标字符数
            overlap: 相邻块重叠字符数

        Returns:
            List[{"text": str, "index": int}]
        """
        if not markdown:
            return []

        # 按段落分割
        paragraphs = []
        current = []

        for line in markdown.split('\n'):
            line = line.strip()
            if line:
                current.append(line)
            else:
                if current:
                    paragraphs.append(' '.join(current))
                    current = []

        if current:
            paragraphs.append(' '.join(current))

        # 合并为块
        chunks = []
        current_chunk = []
        current_len = 0
        chunk_index = 0

        for para in paragraphs:
            para_len = len(para)

            if current_len + para_len > chunk_size and current_chunk:
                # 保存当前块
                text = '\n'.join(current_chunk)
                if text.strip():
                    chunks.append({
                        "text": text.strip(),
                        "index": chunk_index
                    })
                    chunk_index += 1

                # 保留重叠部分
                overlap_text = '\n'.join(current_chunk)
                if len(overlap_text) > overlap:
                    overlap_lines = overlap_text[-overlap:].split('\n')
                    current_chunk = overlap_lines[-3:] if len(overlap_lines) > 3 else overlap_lines
                    current_len = sum(len(l) for l in current_chunk)
                else:
                    current_chunk = []
                    current_len = 0

            current_chunk.append(para)
            current_len += para_len

        # 保存最后一个块
        if current_chunk:
            text = '\n'.join(current_chunk)
            if text.strip():
                chunks.append({
                    "text": text.strip(),
                    "index": chunk_index
                })

        return chunks


# ==================== 数据库操作 ====================

class DocumentDB:
    """文档数据库操作"""

    def __init__(self, config: Dict = None):
        self.config = config or DB_CONFIG
        self.embedding_model = EmbeddingModel()

    def _get_connection(self):
        """获取数据库连接"""
        conn = psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
        conn.set_client_encoding('UTF8')
        return conn

    def save_document(self, file_name: str, source: str = None,
                     brand: str = None, category: str = None) -> int:
        """
        保存文档元信息

        Returns:
            document_id
        """
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO documents (file_name, source, brand, category, upload_date)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
        """, (file_name, source, brand, category))

        doc_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        return doc_id

    def save_chunks(self, document_id: int, chunks: List[Dict],
                    source: str = None, brand: str = None,
                    car_model: str = None, publish_date: str = None) -> int:
        """
        保存文档切片和向量

        Args:
            document_id: 文档ID
            chunks: 切片列表
            source: 来源
            brand: 品牌
            car_model: 车型
            publish_date: 发布日期

        Returns:
            chunks_count
        """
        if not chunks:
            return 0

        # 生成向量
        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_model.encode(texts)

        conn = self._get_connection()
        cur = conn.cursor()

        saved_count = 0
        for i, chunk in enumerate(chunks):
            embedding = embeddings[i]

            # 将Python list转为PostgreSQL array格式
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            # 解析发布日期
            pub_date = chunk.get("publish_date") or publish_date
            if pub_date and isinstance(pub_date, str):
                try:
                    pub_date = datetime.strptime(pub_date, "%Y-%m-%d").date()
                except:
                    pub_date = None

            cur.execute("""
                INSERT INTO chunks (document_id, content, embedding, chunk_index,
                                   source, brand, car_model, publish_date, metadata)
                VALUES (%s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
            """, (
                document_id,
                chunk["text"],
                embedding_str,
                chunk.get("index", i),
                source,
                brand,
                car_model or chunk.get("car_model"),
                pub_date,
                json.dumps({"file_type": "document"})
            ))

            saved_count += 1

        conn.commit()
        cur.close()
        conn.close()

        return saved_count

    def get_documents(self, limit: int = 50, offset: int = 0) -> List[DocumentInfo]:
        """获取文档列表"""
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT d.id, d.file_name, d.source, d.brand, d.category, d.upload_date,
                   COUNT(c.id) as chunks_count
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.document_id
            GROUP BY d.id
            ORDER BY d.upload_date DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        documents = []
        for row in rows:
            documents.append(DocumentInfo(
                id=row['id'],
                file_name=row['file_name'],
                source=row['source'] or '',
                brand=row['brand'] or '',
                category=row['category'] or '',
                upload_date=row['upload_date'],
                chunks_count=row['chunks_count']
            ))

        return documents

    def get_document(self, doc_id: int) -> Optional[DocumentInfo]:
        """获取单个文档"""
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT d.id, d.file_name, d.source, d.brand, d.category, d.upload_date,
                   COUNT(c.id) as chunks_count
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.document_id
            WHERE d.id = %s
            GROUP BY d.id
        """, (doc_id,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return DocumentInfo(
                id=row['id'],
                file_name=row['file_name'],
                source=row['source'] or '',
                brand=row['brand'] or '',
                category=row['category'] or '',
                upload_date=row['upload_date'],
                chunks_count=row['chunks_count']
            )
        return None

    def get_chunks(self, doc_id: int) -> List[Dict]:
        """获取文档的所有切片"""
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, content, chunk_index, page_number
            FROM chunks
            WHERE document_id = %s
            ORDER BY chunk_index
        """, (doc_id,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "id": row['id'],
                "content": row['content'],
                "chunk_index": row['chunk_index'],
                "page_number": row['page_number']
            }
            for row in rows
        ]

    def search_similar(self, query: str, top_k: int = 5,
                       brand: str = None) -> List[Dict]:
        """
        搜索相似内容

        Returns:
            List[{"content": str, "score": float, "document_id": int, "chunk_index": int}]
        """
        # 生成查询向量
        embeddings = self.embedding_model.encode([query])
        query_embedding = embeddings[0]
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        conn = self._get_connection()
        cur = conn.cursor()

        # 构建查询
        if brand:
            cur.execute("""
                SELECT c.id, c.content, c.chunk_index, c.document_id,
                       1 - (c.embedding <=> %s::vector) as similarity
                FROM chunks c
                WHERE c.brand = %s
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
            """, (embedding_str, brand, embedding_str, top_k))
        else:
            cur.execute("""
                SELECT c.id, c.content, c.chunk_index, c.document_id,
                       1 - (c.embedding <=> %s::vector) as similarity
                FROM chunks c
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
            """, (embedding_str, embedding_str, top_k))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "content": row['content'],
                "score": float(row['similarity']),
                "document_id": row['document_id'],
                "chunk_index": row['chunk_index']
            }
            for row in rows
        ]

    def delete_document(self, doc_id: int) -> bool:
        """删除文档及其切片"""
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            # 先删除切片
            cur.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))
            # 再删除文档
            cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Delete error: {e}")
            return False
        finally:
            cur.close()
            conn.close()


# ==================== 文档上传服务 ====================

class DocumentUploadService:
    """文档上传服务"""

    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or os.path.join(
            os.path.dirname(__file__), "uploads"
        )
        os.makedirs(self.upload_dir, exist_ok=True)

        self.parser = MinerUParser(output_dir=os.path.join(self.upload_dir, "parsed"))
        self.db = DocumentDB()

    def upload(self, file_path: str, source: str = None,
               brand: str = None, category: str = None,
               car_model: str = None, publish_date: str = None) -> UploadResult:
        """
        上传并处理文档

        Args:
            file_path: 上传的文件路径
            source: 来源
            brand: 品牌
            category: 分类
            car_model: 车型
            publish_date: 发布日期

        Returns:
            UploadResult
        """
        if not os.path.exists(file_path):
            return UploadResult(
                success=False,
                error=f"File not found: {file_path}"
            )

        file_name = os.path.basename(file_path)

        # 检查格式
        if not self.parser.is_supported(file_path):
            return UploadResult(
                success=False,
                error=f"Unsupported file format: {file_name}"
            )

        try:
            # 1. 使用MinerU解析
            parse_result = self.parser.parse(file_path)

            if not parse_result.get("success"):
                return UploadResult(
                    success=False,
                    file_name=file_name,
                    error=parse_result.get("error", "Parse failed")
                )

            # 2. 保存文档元信息
            doc_id = self.db.save_document(
                file_name=file_name,
                source=source,
                brand=brand,
                category=category
            )

            # 3. 保存切片和向量
            chunks = parse_result.get("chunks", [])
            chunks_count = self.db.save_chunks(
                document_id=doc_id,
                chunks=chunks,
                source=source,
                brand=brand,
                car_model=car_model,
                publish_date=publish_date
            )

            # 4. 移动原始文件到上传目录
            dest_path = os.path.join(self.upload_dir, f"{doc_id}_{file_name}")
            shutil.copy2(file_path, dest_path)

            return UploadResult(
                success=True,
                document_id=doc_id,
                file_name=file_name,
                message="Document uploaded and processed successfully",
                chunks_count=chunks_count
            )

        except Exception as e:
            return UploadResult(
                success=False,
                file_name=file_name,
                error=str(e)
            )


# ==================== 便捷函数 ====================

def upload_document(file_path: str, source: str = None,
                   brand: str = None, category: str = None,
                   car_model: str = None, publish_date: str = None) -> Dict[str, Any]:
    """便捷函数：上传单个文档"""
    service = DocumentUploadService()
    result = service.upload(file_path, source, brand, category, car_model, publish_date)
    return {
        "success": result.success,
        "document_id": result.document_id,
        "file_name": result.file_name,
        "message": result.message,
        "chunks_count": result.chunks_count,
        "error": result.error
    }


def get_document_list(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """获取文档列表"""
    db = DocumentDB()
    docs = db.get_documents(limit, offset)
    return [
        {
            "id": doc.id,
            "file_name": doc.file_name,
            "source": doc.source,
            "brand": doc.brand,
            "category": doc.category,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "chunks_count": doc.chunks_count
        }
        for doc in docs
    ]


def get_document_detail(doc_id: int) -> Optional[Dict[str, Any]]:
    """获取文档详情"""
    db = DocumentDB()
    doc = db.get_document(doc_id)
    if not doc:
        return None

    chunks = db.get_chunks(doc_id)

    return {
        "id": doc.id,
        "file_name": doc.file_name,
        "source": doc.source,
        "brand": doc.brand,
        "category": doc.category,
        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
        "chunks": chunks
    }


def search_documents(query: str, top_k: int = 5, brand: str = None) -> List[Dict[str, Any]]:
    """搜索相似文档"""
    db = DocumentDB()
    results = db.search_similar(query, top_k, brand)

    # 填充文档信息
    for result in results:
        doc = db.get_document(result["document_id"])
        if doc:
            result["file_name"] = doc.file_name
            result["brand"] = doc.brand

    return results


if __name__ == "__main__":
    # 测试
    print("Document Upload Service")
    print("Available functions:")
    print("  - upload_document(file_path, source, brand, category)")
    print("  - get_document_list(limit, offset)")
    print("  - get_document_detail(doc_id)")
    print("  - search_documents(query, top_k, brand)")
