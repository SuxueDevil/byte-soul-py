"""数据库引擎和会话管理"""
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .settings import settings


class Database:
    """MySQL 异步连接封装：创建连接池 + session 工厂"""

    def __init__(self):
        url = (
            f'mysql+asyncmy://{settings.mysql_user}:{settings.mysql_password}@'
            f'{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}'
        )
        self.engine = create_async_engine(
            url,
            echo=True,
            pool_size=settings.mysql_pool_size,
            pool_recycle=settings.mysql_pool_recycle,
            pool_timeout=settings.mysql_pool_timeout,
            max_overflow=settings.mysql_max_overflow,
        )
        self.sessionmaker = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def session(self):
        """
        获取异步 session，用 async with 自动管理生命周期。
        @yield: AsyncSession 实例，退出上下文时自动 close
        """
        async with self.sessionmaker() as s:
            yield s


database = Database()
