"""RAG 服务：文件上传入库"""
from agent.rag.pipeline import rag_pipeline
from api.schemas.rag import FileDTO


class RagService:
    """RAG 服务层"""

    def ingest(self, file: FileDTO) -> int:
        """
        文档入库。
        @param file: 文件数据
        @return: 入库的 chunk 数量
        """
        # 一、字节转文本
        text = file.content.decode("utf-8")
        # 二、调用管道入库
        return rag_pipeline.ingest(text, file.filename)


# 模块级单例
rag_service = RagService()
