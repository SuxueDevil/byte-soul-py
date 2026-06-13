"""FastAPI 应用入口"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from api.handler.global_exception_handler import register
from api.controller.user_controller import user_router
from api.controller.agent_controller import agent_router
from api.controller.rag_controller import rag_router
from config.settings import settings
from config.logger import logger


# 一、生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info("=" * 50)
    logger.info("ByteSoul Agent 启动")
    logger.info("=" * 50)
    logger.info(f"LLM 模型: {settings.llm_model}")
    logger.info(f"Embedding 模型: {settings.embedding_model} ({settings.embedding_dimensions}维)")
    logger.info(f"Milvus: {settings.milvus_host}:{settings.milvus_port}")
    logger.info(f"Elasticsearch: {settings.es_hosts}")
    logger.info("=" * 50)
    yield
    # 关闭时
    logger.info("ByteSoul Agent 关闭")


# 二、创建 FastAPI 实例
app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)

# 三、注册模块
app.include_router(user_router)
app.include_router(agent_router)
app.include_router(rag_router)
register(app)


# 四、启动应用
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
