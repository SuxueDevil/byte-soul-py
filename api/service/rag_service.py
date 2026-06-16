"""RAG 服务：文件上传入库"""
from dataclasses import dataclass

from agent.rag.pipeline import RAGPipeline, ragPipeline
from api.schemas.rag import FileDTO


@dataclass(frozen=True)
class RagServiceDependencies:
    """RAG 服务依赖"""
    pipeline: RAGPipeline


class RagService:
    """RAG 服务层"""

    def __init__(self, deps: RagServiceDependencies) -> None:
        self.deps = deps

    def ingest(self, file: FileDTO) -> int:
        """
        文档入库。
        @param file: 文件数据
        @return: 入库的 chunk 数量
        """
        # 一、字节转文本
        text = file.content.decode("utf-8")
        # 二、调用管道入库
        return self.deps.pipeline.ingest(text, file.filename)


# 一、模块级单例
ragService = RagService(
    RagServiceDependencies(pipeline=ragPipeline)
)
