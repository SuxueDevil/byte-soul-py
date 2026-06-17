"""数据库、搜索引擎、LLM、Embedding 客户端"""
from contextlib import asynccontextmanager

from elasticsearch import Elasticsearch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr
from pymilvus import MilvusClient
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

# ─────────────────────────── Elasticsearch ───────────────────────────
esTemplate = Elasticsearch(settings.es_hosts)

# ─────────────────────────── Embedding ───────────────────────────
embeddingTemplate = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.embedding_api_key,
    base_url=settings.embedding_base_url,
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
