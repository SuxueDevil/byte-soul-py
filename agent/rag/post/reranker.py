"""重排序器：用 Cross-Encoder 对融合结果重新打分"""
from sentence_transformers import CrossEncoder
from config.settings import settings
from config.logger import logger


class Reranker:
    """重排序器：Cross-Encoder 精排"""

    def __init__(self):
        self.model = CrossEncoder(settings.reranker_model)

    # ─────────────────────────── 重排序 ───────────────────────────
    def rerank(self, query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
        """重排序：用 Cross-Encoder 对 query-chunk 对打分

        Args:
            query: 用户原始问题
            chunks: 融合后的 chunk 列表 [{pg_id, rrf_score, source}, ...]
            top_k: 返回数量

        Returns:
            重排序后的结果 [{pg_id, rerank_score, source}, ...]
        """
        if not chunks:
            return []

        # 一、构造 query-chunk 对
        pairs = [(query, chunk.get("content", "")) for chunk in chunks]

        # 二、Cross-Encoder 打分
        scores = self.model.predict(pairs)

        # 三、合并分数，按 rerank_score 降序
        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i])
            chunk["source"] = "rerank"

        results = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
        logger.info(f"[Reranker] {len(chunks)} 条 → 重排序 → Top {len(results)} 条")
        return results


# 模块级单例
reranker = Reranker()
