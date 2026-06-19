"""入库器：PG（ORM）→ Milvus（向量）→ ES（索引）三库写入"""
import hashlib

from langchain_core.documents import Document

from api.models.rag import BSRagChunk
from config.database import pgTemplate, milvusTemplate, esTemplate, embeddingTemplate, snowflakeTemplate
from config.settings import settings
from config.logger import logger


class Saver:
    """入库器：父子模式，PG 写父块+子块，Milvus/ES 只写子块"""

    @staticmethod
    async def save(chunks: list[Document], file_name: str) -> int:
        """入库 chunk

        Args:
            chunks: spliter 切割后的子块 Document 列表
            file_name: 原始文件名

        Returns:
            实际入库的子块数量
        """
        if not chunks:
            return 0

        doc_hash = Saver._calc_doc_hash(chunks)
        logger.info(f"[Saver] 开始入库: {file_name} doc_hash={doc_hash} 子块={len(chunks)}")

        # 一、提取父块，写入 PG
        parent_pg_ids = await Saver._save_parents_to_pg(chunks, doc_hash, file_name)

        # 二、子块写入 PG，拿到 pg_id 列表
        child_pg_ids = await Saver._save_children_to_pg(chunks, doc_hash, file_name, parent_pg_ids)

        # 三、子块生成 embedding，写入 Milvus
        Saver._save_to_milvus(chunks, child_pg_ids, doc_hash)

        # 四、子块写入 ES
        Saver._save_to_es(chunks, child_pg_ids, doc_hash)

        logger.info(f"[Saver] 入库完成: {file_name} → {len(child_pg_ids)} 个子块")
        return len(child_pg_ids)

    @staticmethod
    def _calc_doc_hash(chunks: list[Document]) -> str:
        """计算文档哈希（所有子块内容拼接后取 MD5）"""
        content = "".join(c.page_content for c in chunks)
        return hashlib.md5(content.encode()).hexdigest()

    @staticmethod
    async def _save_parents_to_pg(
        chunks: list[Document], doc_hash: str, file_name: str
    ) -> dict[int, int]:
        """提取父块并写入 PG

        Returns:
            {parent_index: pg_id} 映射
        """
        # 一、从子块 metadata 中提取去重的父块
        parent_map: dict[int, str] = {}
        for chunk in chunks:
            parent_index = chunk.metadata.get("parent_index")
            parent_content = chunk.metadata.get("parent_content")
            if parent_index is not None and parent_index not in parent_map:
                parent_map[parent_index] = parent_content or ""

        # 二、逐个写入 PG（ORM）
        parent_pg_ids: dict[int, int] = {}
        async with pgTemplate.session() as session:
            for parent_index, content in parent_map.items():
                pg_id = snowflakeTemplate.next_id()
                chunk = BSRagChunk(
                    id=pg_id,
                    doc_hash=doc_hash,
                    file_name=file_name,
                    content=content,
                    chunk_index=parent_index,
                    chunk_type="parent",
                )
                session.add(chunk)
                parent_pg_ids[parent_index] = pg_id
            await session.commit()

        logger.info(f"[Saver] 父块入库: {len(parent_pg_ids)} 个")
        return parent_pg_ids

    @staticmethod
    async def _save_children_to_pg(
        chunks: list[Document],
        doc_hash: str,
        file_name: str,
        parent_pg_ids: dict[int, int],
    ) -> list[int]:
        """子块批量写入 PG

        Returns:
            子块 pg_id 列表（与 chunks 顺序对应）
        """
        child_pg_ids: list[int] = []
        async with pgTemplate.session() as session:
            for i, chunk in enumerate(chunks):
                parent_index = chunk.metadata.get("parent_index")
                parent_pg_id = parent_pg_ids.get(parent_index) if parent_index is not None else None
                pg_id = snowflakeTemplate.next_id()

                child = BSRagChunk(
                    id=pg_id,
                    doc_hash=doc_hash,
                    file_name=file_name,
                    content=chunk.page_content,
                    chunk_index=i,
                    parent_id=parent_pg_id,
                    chunk_type="child",
                )
                session.add(child)
                child_pg_ids.append(pg_id)
            await session.commit()

        logger.info(f"[Saver] 子块入库: {len(child_pg_ids)} 个")
        return child_pg_ids

    @staticmethod
    def _save_to_milvus(
        chunks: list[Document], child_pg_ids: list[int], doc_hash: str
    ) -> None:
        """子块生成 embedding 并写入 Milvus"""
        # 一、批量生成向量
        texts = [c.page_content for c in chunks]
        vectors = embeddingTemplate.embed_documents(texts)

        # 二、构造 Milvus 数据
        data = [
            {"pg_id": pg_id, "doc_hash": doc_hash, "vector": vec}
            for pg_id, vec in zip(child_pg_ids, vectors)
        ]

        # 三、批量写入
        milvusTemplate.insert(
            collection_name=settings.milvus_collection,
            data=data,
        )
        logger.info(f"[Saver] Milvus 入库: {len(data)} 条")

    @staticmethod
    def _save_to_es(
        chunks: list[Document], child_pg_ids: list[int], doc_hash: str
    ) -> None:
        """子块写入 ES BM25 索引"""
        # 一、构造 ES 批量请求
        actions = []
        for pg_id, chunk in zip(child_pg_ids, chunks):
            actions.append({"index": {"_index": settings.es_index_name, "_id": str(pg_id)}})
            actions.append({
                "pg_id": pg_id,
                "doc_hash": doc_hash,
                "content": chunk.page_content,
            })

        # 二、批量写入
        esTemplate.bulk(body=actions)
        logger.info(f"[Saver] ES 入库: {len(child_pg_ids)} 条")
