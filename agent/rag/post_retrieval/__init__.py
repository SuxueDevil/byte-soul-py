"""检索后：融合与重排序"""


class RRFFuser:
    """RRF 融合：多路结果加权合并"""

    def fuse(self, *retrieval_results: list[dict], top_k: int = 5) -> list[dict]:
        """RRF 融合

        Args:
            retrieval_results: 多路检索结果
            top_k: 返回数量

        Returns:
            融合后的结果
        """
        # TODO: 实现 RRF 融合算法
        merged = []
        for results in retrieval_results:
            merged.extend(results)
        return merged[:top_k]


class Reranker:
    """重排序：Cross-Encoder 精排"""

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        """重排序

        Args:
            query: 查询
            documents: 文档列表
            top_k: 返回数量

        Returns:
            重排序后的文档
        """
        # TODO: 接入 Cross-Encoder
        return documents[:top_k]


# 模块级单例
rrf_fuser = RRFFuser()
reranker = Reranker()
