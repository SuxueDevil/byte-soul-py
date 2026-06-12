"""查询改写：将口语化问题改写为适合检索的正式表述"""
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from config.settings import settings


def _parse_content(content: str | list) -> str:
    """解析 LLM 返回内容，兼容字符串和结构化输出"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content)


class QueryRewriter:
    """查询改写器：优化查询以提升检索效果"""

    def __init__(self):
        """初始化查询改写器"""
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=SecretStr(settings.llm_api_key),
            base_url=settings.llm_base_url,
            temperature=0,
        )
        self._prompt = """你是一个查询优化专家。请将用户的口语化问题改写为更适合文档检索的正式表述。

要求：
1. 保留原始问题的核心意图
2. 使用更正式、更精确的词汇
3. 去除口语化表达和冗余信息
4. 输出改写后的查询，不要输出其他内容

用户问题：{query}

改写后的查询："""

    def rewrite(self, query: str) -> str:
        """
        改写查询。
        @param query: 原始查询
        @return: 改写后的查询
        """
        response = self._llm.invoke(self._prompt.format(query=query))
        return _parse_content(response.content).strip()

    async def arewrite(self, query: str) -> str:
        """
        异步改写查询。
        @param query: 原始查询
        @return: 改写后的查询
        """
        response = await self._llm.ainvoke(self._prompt.format(query=query))
        return _parse_content(response.content).strip()


# 模块级单例
query_rewriter = QueryRewriter()
