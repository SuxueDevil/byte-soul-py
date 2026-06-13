"""向量检索器：多 query 批量检索 Milvus"""
from config.logger import logger
from .embeddings import embedding_model
from .vectorstore import vectorstore


class VectorRetriever:
    """向量检索器：接收多个 query，embedding 后检索 Milvus"""

    def search(self, queries: list[str], top_k: int = 5) -> list[dict]:
        """
        多 query 向量检索。
        @param queries: 查询列表（来自检索前扩展）
        @param top_k: 每个 query 返回数量
        @return: 合并去重后的结果 [{pg_id, content, score, source}, ...]
        """
        all_hits = []

        for query in queries:
            # 一、query → embedding
            embedding = embedding_model.embed_query(query)

            # 二、Milvus 检索
            hits = vectorstore.search(embedding, top_k)
            all_hits.extend(hits)

        # 三、按 pg_id 去重，保留最高分
        seen = {}
        for hit in all_hits:
            pg_id = hit.get("pg_id")
            if pg_id is None:
                continue
            if pg_id not in seen or hit["score"] > seen[pg_id]["score"]:
                seen[pg_id] = hit

        results = list(seen.values())
        logger.info(f"向量检索: {len(queries)} 个 query → {len(results)} 条结果")
        return results


# 模块级单例
vector_retriever = VectorRetriever()
