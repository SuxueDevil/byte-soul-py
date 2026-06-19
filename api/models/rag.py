"""RAG 文档 ORM 模型，映射到 PostgreSQL bs_rag_chunks 表"""
from datetime import datetime

from sqlalchemy import BigInteger, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from api.models.user import Base


class BSRagChunk(Base):
    """RAG 文档块表"""
    __tablename__ = "bs_rag_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # 雪花 ID
    doc_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(512), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("bs_rag_chunks.id"), nullable=True, index=True)
    chunk_type: Mapped[str] = mapped_column(String(16), default="parent")
    section_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
