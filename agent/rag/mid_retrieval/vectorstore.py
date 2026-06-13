"""Milvus 向量存储封装"""
from pymilvus import MilvusClient, DataType, CollectionSchema, FieldSchema
from config.settings import settings
from config.logger import logger


class VectorStore:
    """Milvus 向量存储：管理集合、插入、检索、删除"""

    def __init__(self):
        # 一、连接 Milvus
        uri = f"http://{settings.milvus_host}:{settings.milvus_port}"
        self.client = MilvusClient(uri=uri)
        self.collection = settings.milvus_collection
        self.dimension = settings.embedding_dimensions
        logger.info(f"Milvus 已连接: {uri}")

        # 二、确保集合存在
        self.ensure_collection()

    def ensure_collection(self):
        """确保集合存在，不存在则创建"""
        if self.client.has_collection(self.collection):
            return

        # 一、定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="pg_id", dtype=DataType.INT64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="doc_hash", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
        ]

        # 二、创建集合
        schema = CollectionSchema(fields=fields, enable_dynamic_field=True)
        self.client.create_collection(
            collection_name=self.collection,
            schema=schema,
        )

        # 三、创建向量索引
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )
        self.client.create_index(
            collection_name=self.collection,
            index_params=index_params,
        )
        logger.info(f"Milvus 集合已创建: {self.collection}, 维度={self.dimension}")

    def insert(self, pg_id: int, content: str, embedding: list[float], doc_hash: str = ""):
        """
        插入一条向量。
        @param pg_id: PostgreSQL 主键
        @param content: 文本内容
        @param embedding: 向量
        @param doc_hash: 文档哈希
        """
        self.client.insert(
            collection_name=self.collection,
            data=[{
                "pg_id": pg_id,
                "content": content,
                "doc_hash": doc_hash,
                "vector": embedding,
            }],
        )

    def insert_batch(self, records: list[dict]):
        """
        批量插入向量。
        @param records: [{pg_id, content, vector, doc_hash}, ...]
        """
        if not records:
            return
        self.client.insert(
            collection_name=self.collection,
            data=records,
        )
        logger.info(f"Milvus 批量插入: {len(records)} 条")

    def search(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        向量相似度检索。
        @param embedding: 查询向量
        @param top_k: 返回数量
        @return: [{pg_id, content, score}, ...]
        """
        results = self.client.search(
            collection_name=self.collection,
            data=[embedding],
            limit=top_k,
            output_fields=["pg_id", "content"],
        )

        hits = []
        for result in results[0]:
            entity = result.get("entity", {})
            hits.append({
                "pg_id": entity.get("pg_id"),
                "content": entity.get("content", ""),
                "score": result.get("distance", 0.0),
                "source": "vector",
            })
        return hits

    def delete(self, pg_id: int):
        """
        按 pg_id 删除向量。
        @param pg_id: PostgreSQL 主键
        """
        self.client.delete(
            collection_name=self.collection,
            filter=f"pg_id == {pg_id}",
        )

    def delete_by_doc_hash(self, doc_hash: str):
        """
        按文档哈希删除所有相关向量。
        @param doc_hash: 文档哈希
        """
        self.client.delete(
            collection_name=self.collection,
            filter=f'doc_hash == "{doc_hash}"',
        )
        logger.info(f"Milvus 删除文档: {doc_hash}")


# 模块级单例
vectorstore = VectorStore()
