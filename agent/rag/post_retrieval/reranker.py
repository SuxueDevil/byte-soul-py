"""Cross-Encoder 重排序：精排提升检索精度"""
from langchain_core.documents import Document
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from config.settings import settings


class Reranker:
    """重排序器：使用 Cross-Encoder 对文档精排"""

    def __init__(self, model_name: str = "", top_k: int = 0):
        """
        初始化重排序器。
        @param model_name: Cross-Encoder 模型名称
        @param top_k: 返回文档数量
        """
        self.model_name = model_name or settings.reranker_model
        self.top_k = top_k or settings.retrieval_top_k
        self._model: HuggingFaceCrossEncoder | None = None
        self._reranker: CrossEncoderReranker | None = None

    def _init(self):
        """懒加载模型"""
        if self._model is None:
            self._model = HuggingFaceCrossEncoder(model_name=self.model_name)
            self._reranker = CrossEncoderReranker(model=self._model, top_n=self.top_k)

    def rerank(self, query: str, documents: list[Document]) -> list[Document]:
        """
        对文档重排序。
        @param query: 查询文本
        @param documents: 文档列表
        @return: 重排序后的文档列表
        """
        if not documents:
            return []

        self._init()
        assert self._reranker is not None
        return self._reranker.compress_documents(documents, query)

    async def arerank(self, query: str, documents: list[Document]) -> list[Document]:
        """
        异步重排序（同步实现）。
        @param query: 查询文本
        @param documents: 文档列表
        @return: 重排序后的文档列表
        """
        return self.rerank(query, documents)


# 模块级单例
reranker = Reranker()
