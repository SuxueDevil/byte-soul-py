"""查询扩展：生成多个语义相关的查询，扩大召回"""
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from config.settings import settings


class QueryExpander:
    """查询扩展器：生成多个相关查询以扩大召回范围"""

    def __init__(self, expansion_count: int | None = None):
        """
        初始化查询扩展器。
        @param expansion_count: 扩展查询数量
        """
        self.expansion_count = expansion_count or settings.rag_expansion_count
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=SecretStr(settings.llm_api_key),
            base_url=settings.llm_base_url,
            temperature=0.7,
        )
        self._prompt = """你是一个查询扩展专家。请根据用户问题生成 {count} 个语义相关的查询，用于扩大文档检索范围。

要求：
1. 每个查询应从不同角度表达相同或相关的意图
2. 使用不同的词汇和表达方式
3. 每行一个查询，不要编号
4. 不要输出其他内容

用户问题：{query}

扩展查询："""

    def _parse_content(self, content: str | list) -> str:
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

    def expand(self, query: str) -> list[str]:
        """
        扩展查询。
        @param query: 原始查询
        @return: 扩展查询列表（包含原始查询）
        """
        response = self._llm.invoke(
            self._prompt.format(query=query, count=self.expansion_count)
        )
        content = self._parse_content(response.content)
        expanded = [line.strip() for line in content.strip().split("\n") if line.strip()]
        all_queries = [query] + expanded
        return list(dict.fromkeys(all_queries))  # 保持顺序去重

    async def aexpand(self, query: str) -> list[str]:
        """
        异步扩展查询。
        @param query: 原始查询
        @return: 扩展查询列表（包含原始查询）
        """
        response = await self._llm.ainvoke(
            self._prompt.format(query=query, count=self.expansion_count)
        )
        content = self._parse_content(response.content)
        expanded = [line.strip() for line in content.strip().split("\n") if line.strip()]
        all_queries = [query] + expanded
        return list(dict.fromkeys(all_queries))


# 模块级单例
query_expander = QueryExpander()
