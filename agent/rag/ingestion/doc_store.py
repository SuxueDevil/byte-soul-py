"""文档存储：支持通用模式和父子模式入库"""
import hashlib
from langchain_core.documents import Document
from config.settings import settings
from config.logger import logger
from schemas.rag import ChunkMode


class DocStore:
    """文档存储：负责文档入库到 PostgreSQL、Milvus、Elasticsearch"""

    def get_doc_hash(self, content: str) -> str:
        """计算文档哈希

        Args:
            content: 文档内容

        Returns:
            文档哈希
        """
        return hashlib.md5(content.encode()).hexdigest()

    def ingest(self, documents: list[Document]) -> int:
        """入库文档

        Args:
            documents: 切割后的文档列表

        Returns:
            入库数量
        """
        if not documents:
            return 0

        if settings.rag_chunk_mode == "parent_child":
            return self.ingest_parent_child(documents)
        return self.ingest_general(documents)

    def ingest_general(self, documents: list[Document]) -> int:
        """通用模式入库

        Args:
            documents: 文档列表

        Returns:
            入库数量
        """
        count = 0
        for doc in documents:
            try:
                pg_id = self.save_to_pg(doc)
                if pg_id > 0:
                    self.save_to_milvus(doc, pg_id)
                    self.save_to_es(doc, pg_id)
                    count += 1
            except Exception as e:
                logger.error(f"入库失败: {e}")

        logger.info(f"通用模式入库完成: {count}/{len(documents)}")
        return count

    def ingest_parent_child(self, documents: list[Document]) -> int:
        """父子模式入库

        Args:
            documents: 子块文档列表（metadata 中包含 parent_content）

        Returns:
            入库数量
        """
        parent_map = {}
        for doc in documents:
            parent_index = doc.metadata.get("parent_index", 0)
            if parent_index not in parent_map:
                parent_map[parent_index] = {
                    "content": doc.metadata.get("parent_content", ""),
                    "section_title": doc.metadata.get("section_title", ""),
                    "doc_hash": doc.metadata.get("doc_hash", ""),
                }

        parent_pg_ids = {}
        for parent_index, parent_data in parent_map.items():
            pg_id = self.save_parent_to_pg(parent_data)
            if pg_id > 0:
                parent_pg_ids[parent_index] = pg_id

        logger.info(f"父块入库完成: {len(parent_pg_ids)} 个")

        count = 0
        for doc in documents:
            try:
                parent_index = doc.metadata.get("parent_index", 0)
                parent_pg_id = parent_pg_ids.get(parent_index, 0)
                if parent_pg_id <= 0:
                    continue

                child_pg_id = self.save_child_to_pg(doc, parent_pg_id)
                if child_pg_id > 0:
                    self.save_to_milvus(doc, child_pg_id)
                    self.save_to_es(doc, child_pg_id)
                    count += 1
            except Exception as e:
                logger.error(f"子块入库失败: {e}")

        logger.info(f"父子模式入库完成: {count}/{len(documents)} 个子块")
        return count

    def save_parent_to_pg(self, parent_data: dict) -> int:
        """保存父块到 PostgreSQL

        Args:
            parent_data: 父块数据

        Returns:
            PostgreSQL ID
        """
        # TODO: 实现 PostgreSQL 入库
        logger.info(f"保存父块到 PostgreSQL: {parent_data.get('section_title')}")
        return 1

    def save_child_to_pg(self, doc: Document, parent_pg_id: int) -> int:
        """保存子块到 PostgreSQL

        Args:
            doc: 子块文档
            parent_pg_id: 关联的父块 ID

        Returns:
            PostgreSQL ID
        """
        # TODO: 实现 PostgreSQL 入库
        logger.info(f"保存子块到 PostgreSQL: parent_id={parent_pg_id}")
        return 1

    def save_to_pg(self, doc: Document) -> int:
        """保存通用块到 PostgreSQL

        Args:
            doc: 文档

        Returns:
            PostgreSQL ID
        """
        # TODO: 实现 PostgreSQL 入库
        logger.info(f"保存到 PostgreSQL: {doc.metadata.get('section_title')}")
        return 1

    def save_to_milvus(self, doc: Document, pg_id: int):
        """保存向量到 Milvus

        Args:
            doc: 文档
            pg_id: PostgreSQL ID
        """
        # TODO: 实现 Milvus 入库
        logger.info(f"保存到 Milvus: pg_id={pg_id}")

    def save_to_es(self, doc: Document, pg_id: int):
        """保存到 Elasticsearch

        Args:
            doc: 文档
            pg_id: PostgreSQL ID
        """
        # TODO: 实现 Elasticsearch 入库
        logger.info(f"保存到 Elasticsearch: pg_id={pg_id}")


# 模块级单例
doc_store = DocStore()
