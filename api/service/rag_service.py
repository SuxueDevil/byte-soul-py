"""RAG 服务：文件上传入库"""
from agent.rag.pipeline import ragPipeline


class RagService:
    """RAG 服务层"""

    def ingest(self, filename: str, content: bytes) -> int:
        """文档入库

        Args:
            filename: 文件名
            content: 文件内容（bytes）

        Returns:
            入库的 chunk 数量
        """
        return ragPipeline.ingest(filename, content.decode("utf-8"))


ragService = RagService()
