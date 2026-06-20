"""检索器：向量检索（Milvus）+ BM25 检索（ES）"""
from config.database import milvusTemplate, esTemplate, embeddingTemplate
from config.settings import settings
from config.logger import logger


class Retriever:
    """多路检索器：向量检索 + BM25 检索"""

    # ─────────────────────────── 向量检索 ───────────────────────────
    def vector_search(self, queries: list[str]) -> list[dict]:
        """向量检索：查询文本 → embedding → Milvus

        Args:
            queries: 查询文本列表

        Returns:
            [{pg_id, score, source}, ...]
        """

        all_hits = []
        for query in queries:
            # 一、查询文本转向量
            vector = embeddingTemplate.embed_query(query)
            # 二、Milvus 向量检索
            res = milvusTemplate.search(
                collection_name=settings.milvus_collection,
                data=[vector],
                limit=settings.retrieval_top_k,
                output_fields=["pg_id"],
            )
            # 三、提取结果
            for hit in res[0]:
                entity = hit.get("entity", {})
                all_hits.append({
                    "pg_id": entity.get("pg_id"),
                    "score": hit.get("distance", 0.0),
                    "source": "vector",
                })
        return self.dedup(all_hits)

    # ─────────────────────────── BM25 检索 ───────────────────────────
    def bm25_search(self, queries: list[str]) -> list[dict]:
        """BM25 检索：查询文本 → ES 关键词匹配

        Args:
            queries: 查询文本列表

        Returns:
            [{pg_id, score, source}, ...]
        """
        all_hits = []
        for query in queries:
            # 一、构造 ES 查询（IK 分词）
            body = {
                "query": {"match": {"content": {"query": query, "analyzer": settings.es_ik_search_analyzer}}},
                "size": settings.retrieval_top_k
            }
            # 二、ES 检索
            res = esTemplate.search(index=settings.es_index_name, body=body)
            # 三、提取结果
            for hit in res.get("hits", {}).get("hits", []):
                all_hits.append({
                    "pg_id": hit.get("_source", {}).get("pg_id"),
                    "score": hit.get("_score", 0.0),
                    "source": "bm25",
                })
        return self.dedup(all_hits)

    # ─────────────────────────── 去重 ───────────────────────────
    @staticmethod
    def dedup(hits: list[dict]) -> list[dict]:
        """按 pg_id 去重，保留最高分

        Args:
            hits: 检索结果列表

        Returns:
            去重后的结果列表
        """
        seen = {}
        for hit in hits:
            pg_id = hit.get("pg_id")
            if pg_id is None:
                continue
            if pg_id not in seen or hit["score"] > seen[pg_id]["score"]:
                seen[pg_id] = hit
        return list(seen.values())


# 模块级单例
retriever = Retriever()
