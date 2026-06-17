"""数据库与搜索引擎客户端"""
from contextlib import asynccontextmanager

from elasticsearch import Elasticsearch
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
