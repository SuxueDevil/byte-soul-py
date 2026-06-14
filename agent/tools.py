"""工具定义：使用 LangChain @tool 装饰器"""
from langchain_core.tools import tool
from agent.rag.pipeline import get_rag_pipeline


@tool
def rag_search(query: str) -> str:
    """在知识库中检索相关信息，用于回答用户的专业问题。

    Args:
        query: 检索关键词，应该是与用户问题相关的核心术语
    """
    if not query:
        return "请提供检索关键词"
    try:
        result = get_rag_pipeline().query(query)
        return result if result else "未找到相关信息"
    except Exception as e:
        return f"检索失败: {str(e)}"


# 工具列表
tools = [rag_search]
