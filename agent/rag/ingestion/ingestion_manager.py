"""入库管理器：将切割后的文档存入多个存储"""
import hashlib
import json
from dataclasses import dataclass
from langchain_core.documents import Document
from config.settings import settings
from config.logger import logger


@dataclass
class ChunkRecord:
    """入库记录"""
    doc_hash: str
    chunk_index: int
    content: str
    metadata: dict
    embedding: list[float]


class IngestionManager:
    """入库管理器：负责文档入库到 PostgreSQL、Milvus、Elasticsearch"""

    def __init__(self):
        """初始化入库管理器"""
        self._pg_conn = None
        self._milvus_client = None
        self._es_client = None

    def _get_doc_hash(self, file_path: str) -> str:
        """
        计算文档哈希。
        @param file_path: 文件路径
        @return: 文档哈希
        """
        with open(file_path, "rb") as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()

    def ingest(self, documents: list[Document], embeddings: list[list[float]]) -> int:
        """
        入库文档。
        @param documents: 切割后的文档列表
        @param embeddings: 对应的向量列表
        @return: 入库数量
        """
        if not documents:
            return 0

        count = 0
        for doc, embedding in zip(documents, embeddings):
            try:
                # 构建入库记录
                record = ChunkRecord(
                    doc_hash=doc.metadata.get("doc_hash", ""),
                    chunk_index=doc.metadata.get("chunk_index", 0),
                    content=doc.page_content,
                    metadata=doc.metadata,
                    embedding=embedding,
                )

                # 入库到 PostgreSQL
                pg_id = self._save_to_pg(record)
                if pg_id > 0:
                    record.metadata["pg_id"] = pg_id

                    # 入库到 Milvus
                    self._save_to_milvus(record)

                    # 入库到 Elasticsearch
                    self._save_to_es(record)

                    count += 1

            except Exception as e:
                logger.error(f"入库失败: {e}")

        logger.info(f"入库完成: {count}/{len(documents)}")
        return count

    def _save_to_pg(self, record: ChunkRecord) -> int:
        """
        保存到 PostgreSQL。
        @param record: 入库记录
        @return: PostgreSQL ID
        """
        # TODO: 实现 PostgreSQL 入库
        logger.info(f"保存到 PostgreSQL: {record.doc_hash}:{record.chunk_index}")
        return 1  # 临时返回

    def _save_to_milvus(self, record: ChunkRecord):
        """
        保存到 Milvus。
        @param record: 入库记录
        """
        # TODO: 实现 Milvus 入库
        logger.info(f"保存到 Milvus: {record.doc_hash}:{record.chunk_index}")

    def _save_to_es(self, record: ChunkRecord):
        """
        保存到 Elasticsearch。
        @param record: 入库记录
        """
        # TODO: 实现 Elasticsearch 入库
        logger.info(f"保存到 Elasticsearch: {record.doc_hash}:{record.chunk_index}")


# 模块级单例
ingestion_manager = IngestionManager()
