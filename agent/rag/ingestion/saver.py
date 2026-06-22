"""入库器：PG（ORM）→ Milvus（向量）→ ES（索引）三库写入"""
import hashlib

from langchain_core.documents import Document

from api.models.rag import BSRagChunk
from config.database import pgTemplate, milvusTemplate, esTemplate, embeddingTemplate, snowflakeTemplate
from config.settings import settings
from config.logger import logger
from sqlalchemy import select, delete


class Saver:
    """入库器：父子模式，PG 写父块+子块，Milvus/ES 只写子块"""

    # ─────────────────────────── 入口 ───────────────────────────
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

        doc_hash = Saver.calc_doc_hash(chunks)
        logger.info(f"[Saver] 开始入库: {file_name} doc_hash={doc_hash} 子块={len(chunks)}")

        # 一、去重：doc_hash 已存在则三库联删
        await Saver.delete_if_exists(doc_hash)

        # 二、提取父块，写入 PG
        parent_pg_ids = await Saver.save_parents_to_pg(chunks, doc_hash, file_name)

        # 三、子块写入 PG，拿到 pg_id 列表
        child_pg_ids = await Saver.save_children_to_pg(chunks, doc_hash, file_name, parent_pg_ids)

        # 四、子块生成 embedding，写入 Milvus
        Saver.save_to_milvus(chunks, child_pg_ids, doc_hash)

        # 五、子块写入 ES TODO，测试暂时关闭
        # Saver.save_to_es(chunks, child_pg_ids, doc_hash)

        logger.info(f"[Saver] 入库完成: {file_name} → {len(child_pg_ids)} 个子块")
        return len(child_pg_ids)

    # ─────────────────────────── PG 写入 ───────────────────────────
    @staticmethod
    async def save_parents_to_pg(
        chunks: list[Document], doc_hash: str, file_name: str
    ) -> dict[int, int]:
        """提取父块并写入 PG

        Args:
            chunks: 子块 Document 列表
            doc_hash: 文档哈希
            file_name: 原始文件名

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
    async def save_children_to_pg(
        chunks: list[Document],
        doc_hash: str,
        file_name: str,
        parent_pg_ids: dict[int, int],
    ) -> list[int]:
        """子块批量写入 PG

        Args:
            chunks: 子块 Document 列表
            doc_hash: 文档哈希
            file_name: 原始文件名
            parent_pg_ids: {parent_index: pg_id} 映射

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

    # ─────────────────────────── Milvus 写入 ───────────────────────────
    @staticmethod
    def save_to_milvus(
        chunks: list[Document], child_pg_ids: list[int], doc_hash: str
    ) -> None:
        """子块生成 embedding 并写入 Milvus

        Args:
            chunks: 子块 Document 列表
            child_pg_ids: 子块 pg_id 列表
            doc_hash: 文档哈希
        """
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

    # ─────────────────────────── ES 写入 ───────────────────────────
    @staticmethod
    def save_to_es(
        chunks: list[Document], child_pg_ids: list[int], doc_hash: str
    ) -> None:
        """子块写入 ES BM25 索引

        Args:
            chunks: 子块 Document 列表
            child_pg_ids: 子块 pg_id 列表
            doc_hash: 文档哈希
        """
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

    # ─────────────────────────── 去重 ───────────────────────────
    @staticmethod
    def calc_doc_hash(chunks: list[Document]) -> str:
        """计算文档哈希（所有子块内容拼接后取 MD5）

        Args:
            chunks: 子块 Document 列表

        Returns:
            MD5 哈希字符串
        """
        content = "".join(c.page_content for c in chunks)
        return hashlib.md5(content.encode()).hexdigest()

    @staticmethod
    async def delete_if_exists(doc_hash: str) -> None:
        """doc_hash 已存在则三库联删

        Args:
            doc_hash: 文档哈希
        """
        async with pgTemplate.session() as session:
            result = await session.execute(
                select(BSRagChunk.id).where(BSRagChunk.doc_hash == doc_hash)
            )
            pg_ids = [row[0] for row in result.fetchall()]

        if not pg_ids:
            return

        logger.info(f"[Saver] 检测到重复文档 doc_hash={doc_hash}，删除旧数据: {len(pg_ids)} 条")

        # 一、PG 删除
        async with pgTemplate.session() as session:
            await session.execute(
                delete(BSRagChunk).where(BSRagChunk.doc_hash == doc_hash)
            )
            await session.commit()

        # 二、Milvus 删除
        milvusTemplate.delete(
            collection_name=settings.milvus_collection,
            filter=f'doc_hash == "{doc_hash}"',
        )

        # 三、ES 删除
        str_ids = [str(i) for i in pg_ids]
        for pg_id in str_ids:
            try:
                esTemplate.delete(index=settings.es_index_name, id=pg_id)
            except Exception:
                pass
