"""向量存储：Chroma 向量数据库封装"""
import os
from langchain_chroma import Chroma
from config.settings import settings
from .embeddings import embeddings


class VectorStoreFactory:
    """向量存储工厂：创建并管理 Chroma 实例"""

    @staticmethod
    def create() -> Chroma:
        """
        创建 Chroma 向量存储实例。
        @return: Chroma 实例
        """
        persist_dir = settings.vectorstore_persist_directory
        os.makedirs(persist_dir, exist_ok=True)

        return Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name="rag_collection",
        )


# 模块级单例
vectorstore = VectorStoreFactory.create()
