"""RAG 服务：文档入库 + 查询"""
from agent.rag.pipeline import ragPipeline
from agent.rag.ingestion.saver import Saver
from api.models.rag import BSRagChunk
from config.database import pgTemplate
from sqlalchemy import select


class RagService:
    """RAG 服务层"""

    async def ingest(self, filename: str, content: bytes) -> int:
        """文档入库

        Args:
            filename: 文件名
            content: 文件内容（bytes）

        Returns:
            入库的 chunk 数量
        """
        return await ragPipeline.ingest(filename, content.decode("utf-8"))

    async def list_documents(self) -> list[dict]:
        """文档列表

        Returns:
            [{doc_hash, file_name, chunk_count}, ...]
        """
        async with pgTemplate.session() as session:
            result = await session.execute(
                select(
                    BSRagChunk.doc_hash,
                    BSRagChunk.file_name,
                ).distinct()
            )
            rows = result.fetchall()

        # 统计每个文档的 chunk 数量
        documents = []
        for row in rows:
            doc_hash, file_name = row
            async with pgTemplate.session() as session:
                count_result = await session.execute(
                    select(BSRagChunk.id).where(BSRagChunk.doc_hash == doc_hash)
                )
                chunk_count = len(count_result.fetchall())
            documents.append({
                "doc_hash": doc_hash,
                "file_name": file_name,
                "chunk_count": chunk_count,
            })
        return documents

    async def get_chunks(self, doc_hash: str) -> list[dict]:
        """获取文档的 chunk 列表

        Args:
            doc_hash: 文档哈希

        Returns:
            [{id, content, chunk_index, parent_id, chunk_type}, ...]
        """
        async with pgTemplate.session() as session:
            result = await session.execute(
                select(BSRagChunk).where(BSRagChunk.doc_hash == doc_hash).order_by(BSRagChunk.chunk_index)
            )
            rows = result.fetchall()

        chunks = []
        for row in rows:
            chunk = row[0]
            chunks.append({
                "id": chunk.id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "parent_id": chunk.parent_id,
                "chunk_type": chunk.chunk_type,
            })
        return chunks

    async def delete_document(self, doc_hash: str) -> int:
        """删除文档（三库联删）

        Args:
            doc_hash: 文档哈希

        Returns:
            删除的 chunk 数量
        """
        # 一、PG 删除
        async with pgTemplate.session() as session:
            result = await session.execute(
                select(BSRagChunk.id).where(BSRagChunk.doc_hash == doc_hash)
            )
            pg_ids = [row[0] for row in result.fetchall()]

        if not pg_ids:
            return 0

        # 二、三库联删
        from agent.rag.ingestion.saver import saver
        await saver.delete_if_exists(doc_hash)
        return len(pg_ids)


ragService = RagService()
