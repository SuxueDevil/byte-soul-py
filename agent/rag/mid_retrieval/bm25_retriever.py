"""BM25 检索器：基于关键词匹配的检索"""
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
import jieba


class BM25Retriever:
    """BM25 检索器：使用 BM25 算法进行关键词检索"""

    def __init__(self, top_k: int = 5):
        """
        初始化 BM25 检索器。
        @param top_k: 返回文档数量
        """
        self.top_k = top_k
        self._documents: list[Document] = []
        self._bm25: BM25Okapi | None = None
        self._tokenized_corpus: list[list[str]] = []

    def fit(self, documents: list[Document]):
        """
        构建 BM25 索引。
        @param documents: 文档列表
        """
        self._documents = documents
        # 使用 jieba 分词
        self._tokenized_corpus = [
            list(jieba.cut(doc.page_content)) for doc in documents
        ]
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    def retrieve(self, query: str) -> list[Document]:
        """
        执行 BM25 检索。
        @param query: 查询文本
        @return: 相关文档列表
        """
        if not self._bm25:
            return []

        # 查询分词
        tokenized_query = list(jieba.cut(query))
        # 计算分数
        scores = self._bm25.get_scores(tokenized_query)
        # 获取 top_k 索引
        top_indices = scores.argsort()[-self.top_k:][::-1]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self._documents[idx]
                doc.metadata["bm25_score"] = float(scores[idx])
                results.append(doc)

        return results

    async def aretrieve(self, query: str) -> list[Document]:
        """
        异步执行 BM25 检索。
        @param query: 查询文本
        @return: 相关文档列表
        """
        return self.retrieve(query)


# 模块级单例
bm25_retriever = BM25Retriever()
