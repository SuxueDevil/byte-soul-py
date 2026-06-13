"""RAG 请求/响应结构"""
from pydantic import BaseModel


class FileDTO(BaseModel):
    """文件上传数据"""
    filename: str
    content: bytes
