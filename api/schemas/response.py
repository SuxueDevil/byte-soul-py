"""统一响应包装：所有接口返回此格式"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class Response(BaseModel):
    """统一 JSON 响应体"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Any = Field(None, description="数据")

    @classmethod
    def success(cls, data: Any = None, message: str = "success", code: int = 200) -> "Response":
        """构建成功响应"""
        return cls(code=code, message=message, data=data)

    @classmethod
    def error(cls, message: str = "error", code: int = 500, data: Any = None) -> "Response":
        """构建错误响应"""
        return cls(code=code, message=message, data=data)
    
class ResponsePage(BaseModel):
    """分页响应体"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: list = Field(default_factory=list, description="数据列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页数量")

    @classmethod
    def success(cls, data: list, total: int, page: int, page_size: int) -> "ResponsePage":
        """构建分页成功响应"""
        return cls(code=200, message="success", data=data, total=total, page=page, page_size=page_size)
