"""数据库、搜索引擎、LLM、Embedding、雪花ID 客户端"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr
from pymilvus import MilvusClient
from sonyflake import Sonyflake
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.settings import settings


class Database:
    """异步数据库连接封装：创建连接池 + session 工厂"""

    def __init__(self, url: str, **kwargs):
        self.engine = create_async_engine(url, **kwargs)
        self.sessionmaker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self):
        """获取异步 session

        Yields:
            AsyncSession 实例；退出上下文时自动 close
        """
        # 一、async with 自动管理 session 生命周期
        # 1、退出上下文自动 close，避免连接泄漏
        async with self.sessionmaker() as s:
            yield s


# ─────────────────────────── MySQL ───────────────────────────
mysqlTemplate = Database(
    url=(
        f"mysql+asyncmy://{settings.mysql_user}:{settings.mysql_password}@"
        f"{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
    ),
    echo=True,
    pool_size=settings.mysql_pool_size,
    pool_recycle=settings.mysql_pool_recycle,
    pool_timeout=settings.mysql_pool_timeout,
    max_overflow=settings.mysql_max_overflow,
)

# ─────────────────────────── PostgreSQL ───────────────────────────
pgTemplate = Database(url=settings.rag_pg_url, echo=True)

# ─────────────────────────── Milvus ───────────────────────────
milvusTemplate = MilvusClient(
    uri=f"http://{settings.milvus_host}:{settings.milvus_port}",
)
milvusTemplate.load_collection(collection_name=settings.milvus_collection)

# ─────────────────────────── Elasticsearch ───────────────────────────
esTemplate = Elasticsearch(settings.es_hosts)

# ─────────────────────────── Embedding ───────────────────────────
"""
对，chunk_size=10 会自动分批。OpenAIEmbeddings 内部逻辑是：
17 条文本 → 按 chunk_size=10 分成两批
  第一批：10 条 → API → 返回 10 个向量
  第二批：7 条 → API → 返回 7 个向量
合并 → 返回 17 个向量
"""
embeddingTemplate = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.embedding_api_key,
    base_url=settings.embedding_base_url,
    tiktoken_enabled=False,
    check_embedding_ctx_length=False,
    chunk_size=10,
)

# ─────────────────────────── LLM ───────────────────────────
# 一、流式实例，供对话等需要流式输出的场景使用
llmTemplate = ChatOpenAI(
    model=settings.llm_model,
    api_key=SecretStr(settings.llm_api_key),
    base_url=settings.llm_base_url,
    streaming=True,
)

# 二、非流式实例，供意图分类等不需要流式输出的场景使用
llmNoStreamTemplate = ChatOpenAI(
    model=settings.llm_model,
    api_key=SecretStr(settings.llm_api_key),
    base_url=settings.llm_base_url,
    streaming=False,
)

# ─────────────────────────── 雪花 ID ───────────────────────────
snowflakeTemplate = Sonyflake(
    start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
    machine_id=1,
)
