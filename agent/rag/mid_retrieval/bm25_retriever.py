"""BM25 检索器：Elasticsearch + IK 分词"""
from elasticsearch import Elasticsearch
from config.settings import settings
from config.logger import logger


class BM25Retriever:
    """BM25 检索器：多 query 检索 Elasticsearch"""

    def __init__(self):
        self.es = Elasticsearch(settings.es_hosts)
        self.index = settings.es_index_name
        logger.info(f"Elasticsearch 已连接: {settings.es_hosts}")

        self.ensure_index()

    def ensure_index(self):
        """确保索引存在，不存在则创建"""
        if self.es.indices.exists(index=self.index):
            return

        mapping = {
            "mappings": {
                "properties": {
                    "pg_id": {"type": "integer"},
                    "content": {
                        "type": "text",
                        "analyzer": settings.es_ik_analyzer,
                        "search_analyzer": settings.es_ik_search_analyzer,
                    },
                    "doc_hash": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                }
            }
        }

        self.es.indices.create(index=self.index, body=mapping)
        logger.info(f"ES 索引已创建: {self.index}")

    def index_doc(self, pg_id: int, content: str, doc_hash: str = "", chunk_index: int = 0):
        """索引一条文档

        Args:
            pg_id: PostgreSQL 主键
            content: 文本内容
            doc_hash: 文档哈希
            chunk_index: 块序号
        """
        self.es.index(
            index=self.index,
            id=str(pg_id),
            body={
                "pg_id": pg_id,
                "content": content,
                "doc_hash": doc_hash,
                "chunk_index": chunk_index,
            },
        )

    def search(self, queries: list[str], top_k: int = 5) -> list[dict]:
        """多 query BM25 检索

        Args:
            queries: 查询列表
            top_k: 每个 query 返回数量

        Returns:
            合并去重后的结果 [{pg_id, content, score, source}, ...]
        """
        all_hits = []

        for query in queries:
            body = {
                "query": {
                    "match": {
                        "content": {
                            "query": query,
                            "analyzer": settings.es_ik_search_analyzer,
                        }
                    }
                },
                "size": top_k,
            }
            resp = self.es.search(index=self.index, body=body)

            for hit in resp.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                all_hits.append({
                    "pg_id": source.get("pg_id"),
                    "content": source.get("content", ""),
                    "score": hit.get("_score", 0.0),
                    "source": "bm25",
                })

        # 按 pg_id 去重，保留最高分
        seen = {}
        for hit in all_hits:
            pg_id = hit.get("pg_id")
            if pg_id is None:
                continue
            if pg_id not in seen or hit["score"] > seen[pg_id]["score"]:
                seen[pg_id] = hit

        results = list(seen.values())
        logger.info(f"BM25 检索: {len(queries)} 个 query → {len(results)} 条结果")
        return results

    def delete(self, pg_id: int):
        """按 pg_id 删除文档

        Args:
            pg_id: PostgreSQL 主键
        """
        try:
            self.es.delete(index=self.index, id=str(pg_id))
        except Exception:
            pass

    def delete_by_doc_hash(self, doc_hash: str):
        """按文档哈希删除所有相关文档

        Args:
            doc_hash: 文档哈希
        """
        self.es.delete_by_query(
            index=self.index,
            body={"query": {"term": {"doc_hash": doc_hash}}},
        )
        logger.info(f"ES 删除文档: {doc_hash}")


# 模块级单例
bm25_retriever = BM25Retriever()
