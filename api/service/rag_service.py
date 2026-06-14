"""RAG 服务：文件上传入库"""
from dataclasses import dataclass
from agent.rag.pipeline import RAGPipeline
from api.schemas.rag import FileDTO


@dataclass
class RagServiceDependencies:
    """RAG 服务依赖"""
    pipeline: RAGPipeline


class RagService:
    """RAG 服务层"""

    def __init__(self, deps: RagServiceDependencies):
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


def get_rag_service() -> RagService:
    """创建 RAG 服务实例（FastAPI Depends 注入点）"""
    from agent.rag.pipeline import rag_pipeline
    deps = RagServiceDependencies(pipeline=rag_pipeline)
    return RagService(deps)
