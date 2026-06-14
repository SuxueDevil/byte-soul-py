"""FastAPI 应用入口"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.handler.global_exception_handler import register
from api.controller.user_controller import user_router
from api.controller.agent_controller import agent_router
from api.controller.rag_controller import rag_router
from config.settings import settings
from config.logger import logger


# 1、创建 FastAPI 实例
app = FastAPI(docs_url=None, redoc_url=None)

# 2、注册模块
app.include_router(user_router)
app.include_router(agent_router)
app.include_router(rag_router)
register(app)

# 3、CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4、启动应用
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
