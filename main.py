"""FastAPI 应用入口"""
import uvicorn
from fastapi import FastAPI
from api.handler.global_exception_handler import register
from api.controller.user_controller import user_router
from api.controller.agent_controller import agent_router
from api.controller.rag_controller import rag_router
from config.settings import settings
from config.logger import logger

# 一、创建 FastAPI 实例
# 1、禁用默认文档接口
app = FastAPI(docs_url=None, redoc_url=None)

# 二、注册模块
# 1、路由注册
app.include_router(user_router)
app.include_router(agent_router)
app.include_router(rag_router)
# 2、全局异常处理
register(app)


# 三、启动事件：打印服务状态
@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("ByteSoul Agent 启动")
    logger.info("=" * 50)
    logger.info(f"LLM 模型: {settings.llm_model}")
    logger.info(f"Embedding 模型: {settings.embedding_model} ({settings.embedding_dimensions}维)")
    logger.info(f"Milvus: {settings.milvus_host}:{settings.milvus_port}")
    logger.info(f"Elasticsearch: {settings.es_hosts}")
    logger.info("=" * 50)


# 四、启动应用
# 1、基于 uvicorn，监听所有接口
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
