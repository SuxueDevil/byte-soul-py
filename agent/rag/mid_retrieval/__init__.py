"""检索中：多路检索"""


class VectorRetriever:
    """向量检索：Milvus 语义相似度"""

    def search(self, queries: list[str], top_k: int = 5) -> list[dict]:
        """
        向量检索。
        @param queries: 查询列表
        @param top_k: 返回数量
        @return: 检索结果
        """
        # TODO: 接入 Milvus
        return []


class BM25Retriever:
    """BM25 检索：Elasticsearch 关键词匹配"""

    def search(self, queries: list[str], top_k: int = 5) -> list[dict]:
        """
        BM25 检索。
        @param queries: 查询列表
        @param top_k: 返回数量
        @return: 检索结果
        """
        # TODO: 接入 Elasticsearch
        return []


class ContextCompressor:
    """上下文压缩：提取相关片段"""

    def compress(self, query: str, documents: list[dict]) -> list[dict]:
        """
        压缩文档。
        @param query: 查询
        @param documents: 文档列表
        @return: 压缩后的文档
        """
        # TODO: 接入 LLM 压缩
        return documents


# 模块级单例
vector_retriever = VectorRetriever()
bm25_retriever = BM25Retriever()
context_compressor = ContextCompressor()
