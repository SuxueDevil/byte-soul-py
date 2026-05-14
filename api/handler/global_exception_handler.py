"""全局异常处理器，统一记录日志并返回标准 JSON 响应"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from config.logger import logger
from api.schemas.response import Response


def register(app: FastAPI):
    """注册所有异常处理器到 FastAPI 实例"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        捕获 Pydantic 校验失败异常，记录详情后返回 422。
        @param request: 触发异常的请求
        @param exc: 校验异常，包含 errors() 详情
        @return: JSONResponse，状态码 422
        """
        # 一、记录并响应
        # 1、记录校验失败详情
        logger.warning("Validation error at {}: {}", request.url, exc.errors())
        # 2、返回标准 422 响应
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        全局异常兜底：捕获所有未被中间层处理的异常。
        @param request: 触发异常的请求
        @param exc: 未被捕获的异常对象
        @return: 统一错误响应
        """
        # 一、记录并响应
        # 1、记录异常及堆栈
        logger.exception("Unhandled error at {}", request.url)
        # 2、返回统一 JSON 错误响应
        return Response.error(message="Internal server error")
