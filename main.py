"""FastAPI 应用入口"""
import uvicorn
from fastapi import FastAPI
from api.handler.global_exception_handler import register
from api.controller.user_controller import user_router
from api.controller.agent_controller import agent_router
from api.controller.rag_controller import rag_router

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

# 三、启动应用
# 1、基于 uvicorn，监听所有接口
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
