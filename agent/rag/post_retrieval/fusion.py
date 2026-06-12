"""RRF 结果融合：多路检索结果加权合并"""
from langchain_core.documents import Document


class RRFFuser:
    """RRF (Reciprocal Rank Fusion) 融合器：合并多路检索结果"""

    def __init__(self, k: int = 60):
        """
        初始化 RRF 融合器。
        @param k: RRF 参数，控制排名靠后的文档权重衰减速度
        """
        self.k = k

    def fuse(self, *retrieval_results: list[Document], weights: list[float] = None) -> list[Document]:
        """
        融合多路检索结果。
        @param retrieval_results: 多路检索结果，每路是 Document 列表
        @param weights: 各路权重，默认相等
        @return: 融合后的 Document 列表（按 RRF 分数降序）
        """
        if not retrieval_results:
            return []

        # 默认权重相等
        num_results = len(retrieval_results)
        if weights is None:
            weights = [1.0 / num_results] * num_results

        # 计算 RRF 分数：score = sum(weight / (k + rank))
        doc_scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        for results, weight in zip(retrieval_results, weights):
            for rank, doc in enumerate(results):
                doc_id = self._get_doc_id(doc)
                rrf_score = weight / (self.k + rank + 1)

                doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
                doc_map[doc_id] = doc

        # 按 RRF 分数降序排序
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # 构建结果，附加 RRF 分数
        results = []
        for doc_id, score in sorted_docs:
            doc = doc_map[doc_id]
            doc.metadata["rrf_score"] = score
            results.append(doc)

        return results

    @staticmethod
    def _get_doc_id(doc: Document) -> str:
        """
        生成文档唯一标识（用于去重）。
        @param doc: Document 对象
        @return: 文档 ID
        """
        # 使用内容哈希 + 来源作为唯一标识
        content_hash = hash(doc.page_content[:100])
        source = doc.metadata.get("source", "")
        return f"{source}:{content_hash}"


# 模块级单例
rrf_fuser = RRFFuser()
