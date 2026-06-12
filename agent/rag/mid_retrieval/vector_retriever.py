"""向量检索器：基于语义相似度的检索"""
from langchain_core.documents import Document
from .vectorstore import vectorstore
from config.settings import settings


class VectorRetriever:
    """向量检索器：使用 Chroma 进行语义相似度检索"""

    def __init__(self, top_k: int = None, score_threshold: float = None):
        """
        初始化向量检索器。
        @param top_k: 返回文档数量
        @param score_threshold: 相似度阈值（0-1，越大越严格）
        """
        self.top_k = top_k or settings.retrieval_top_k
        self.score_threshold = score_threshold or settings.retrieval_score_threshold
        self._retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": self.top_k,
                "score_threshold": self.score_threshold,
            },
        )

    def retrieve(self, query: str) -> list[Document]:
        """
        执行向量检索。
        @param query: 查询文本
        @return: 相关文档列表
        """
        return self._retriever.invoke(query)

    async def aretrieve(self, query: str) -> list[Document]:
        """
        异步执行向量检索。
        @param query: 查询文本
        @return: 相关文档列表
        """
        return await self._retriever.ainvoke(query)


# 模块级单例
vector_retriever = VectorRetriever()
