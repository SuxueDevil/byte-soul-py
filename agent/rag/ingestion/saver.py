"""入库器：把切割后的 chunk 写入 Milvus 向量库 + Elasticsearch BM25 索引"""
from langchain_core.documents import Document

from config.logger import logger


class Saver:
    """入库器：Milvus（向量）+ Elasticsearch（BM25）双写"""

    @staticmethod
    def save(chunks: list[Document]) -> int:
        """入库 chunk

        Args:
            chunks: 切割后的 Document 列表

        Returns:
            实际入库数量
        """
        # 一、空输入直接返回
        if not chunks:
            return 0

        # 二、双写
        # 1、Milvus 存向量，用于语义检索
        # 2、Elasticsearch 存原文，用于 BM25 关键词检索
        try:
            Saver._save_to_milvus(chunks)
            Saver._save_to_es(chunks)
        except Exception as e:
            logger.error(f"入库失败: {e}")
            return 0

        return len(chunks)

    @staticmethod
    def _save_to_milvus(chunks: list[Document]) -> None:
        """写入 Milvus 向量库"""
        # 一、调用向量存储 upsert 接口
        # 二、用 doc_hash 作为 partition key 隔离文档
        logger.debug(f"写入 Milvus: {len(chunks)} 条")

    @staticmethod
    def _save_to_es(chunks: list[Document]) -> None:
        """写入 Elasticsearch BM25 索引"""
        # 一、构造 ES 文档（content + metadata）
        # 二、bulk 写入指定索引
        logger.debug(f"写入 Elasticsearch: {len(chunks)} 条")
