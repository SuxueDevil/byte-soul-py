"""RRF 融合：合并向量检索和 BM25 检索的结果"""
from config.logger import logger

# RRF 常量
RRF_K = 60  # RRF 公式中的常数，控制排名权重衰减速度


class Fusion:
    """RRF 融合器：多路检索结果 → 统一排序"""

    # ─────────────────────────── 融合 ───────────────────────────
    def fuse(self, vector_hits: list[dict], bm25_hits: list[dict]) -> list[dict]:
        """RRF 融合：合并向量检索和 BM25 检索结果

        RRF 公式：score = Σ 1/(k + rank_i)

        Args:
            vector_hits: 向量检索结果 [{pg_id, score, source}, ...]
            bm25_hits: BM25 检索结果 [{pg_id, score, source}, ...]

        Returns:
            融合后的结果 [{pg_id, rrf_score, source}, ...]，按 rrf_score 降序
        """
        # 一、为每路结果按 score 降序排名
        vector_ranked = self.rank_by_score(vector_hits)
        bm25_ranked = self.rank_by_score(bm25_hits)

        # 二、计算 RRF 分数
        rrf_scores: dict[int, float] = {}
        for rank, hit in enumerate(vector_ranked):
            pg_id = hit["pg_id"]
            rrf_scores[pg_id] = rrf_scores.get(pg_id, 0.0) + 1.0 / (RRF_K + rank + 1)

        for rank, hit in enumerate(bm25_ranked):
            pg_id = hit["pg_id"]
            rrf_scores[pg_id] = rrf_scores.get(pg_id, 0.0) + 1.0 / (RRF_K + rank + 1)

        # 三、按 RRF 分数降序排序
        results = sorted(
            [{"pg_id": pg_id, "rrf_score": score, "source": "rrf"} for pg_id, score in rrf_scores.items()],
            key=lambda x: x["rrf_score"],
            reverse=True,
        )

        logger.info(f"[Fusion] 向量 {len(vector_hits)} 条 + BM25 {len(bm25_hits)} 条 → 融合 {len(results)} 条")
        return results

    # ─────────────────────────── 排名 ───────────────────────────
    @staticmethod
    def rank_by_score(hits: list[dict]) -> list[dict]:
        """按 score 降序排名

        Args:
            hits: 检索结果列表

        Returns:
            按 score 降序排列的结果列表
        """
        return sorted(hits, key=lambda x: x.get("score", 0), reverse=True)


# 模块级单例
fusion = Fusion()
