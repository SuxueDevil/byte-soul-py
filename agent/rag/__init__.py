"""RAG 模块：文档加载、切割、入库、检索"""
from .ingestion import ingestion_pipeline

__all__ = [
    "ingestion_pipeline",
]
