"""RAG 检索工具"""
from agent.tools.base import BaseTool
from agent.rag.pipeline import rag_pipeline


class RAGTool(BaseTool):
    """RAG 知识库检索工具"""

    name = "rag_search"
    description = "从知识库检索相关信息，输入为查询文本"

    def execute(self, query: str = "", **kwargs) -> str:
        """
        执行 RAG 检索。
        @param query: 查询文本
        @return: 检索结果
        """
        if not query:
            return "错误：请提供查询文本"

        try:
            result = rag_pipeline.query(query)
            return result if result else "未找到相关信息"
        except Exception as e:
            return f"检索失败: {str(e)}"


# 模块级单例
rag_tool = RAGTool()
