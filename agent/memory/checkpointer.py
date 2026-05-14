import asyncio
import os
import aiosqlite
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver
from config.settings import settings


class SqliteMemory:
    """SQLite 短期记忆（同步），适配同步调用链"""

    def __init__(self):
        os.makedirs(os.path.dirname(settings.sqlite_url), exist_ok=True)
        self.checkpointer = SqliteSaver.from_conn_string(settings.sqlite_url).__enter__()


class AsyncSqliteMemory:
    """SQLite 短期记忆（异步），适配 astream_events 等异步调用链"""

    def __init__(self):
        os.makedirs(os.path.dirname(settings.sqlite_url), exist_ok=True)
        # 一、初始化异步 SQLite 连接
        # 1、aiosqlite.connect() 同步返回连接对象
        # 2、AsyncSqliteSaver 内部调用 get_running_loop()，需用 asyncio.run 提供临时事件循环
        async def init_conn():
            return AsyncSqliteSaver(conn=await aiosqlite.connect(settings.sqlite_url))
        self.checkpointer = asyncio.run(init_conn())


class PostgresMemory:
    """PostgreSQL 短期记忆"""

    def __init__(self):
        self.checkpointer = PostgresSaver.from_conn_string(settings.pg_url)


match settings.checkpointer_model:
    case "postgres":
        checkpointer = PostgresMemory().checkpointer
    case "sqlite":
        checkpointer = SqliteMemory().checkpointer
    case "async_sqlite":
        checkpointer = AsyncSqliteMemory().checkpointer
