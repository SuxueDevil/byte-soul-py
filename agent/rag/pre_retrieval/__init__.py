"""检索前：查询优化"""


class QueryRewriter:
    """查询改写：口语化 → 正式表述"""

    def rewrite(self, query: str) -> str:
        """
        改写查询。
        @param query: 原始查询
        @return: 改写后的查询
        """
        # TODO: 接入 LLM 改写
        return query


class QueryExpander:
    """查询扩展：生成多个相关查询"""

    def expand(self, query: str, count: int = 3) -> list[str]:
        """
        扩展查询。
        @param query: 原始查询
        @param count: 扩展数量
        @return: 扩展后的查询列表
        """
        # TODO: 接入 LLM 扩展
        return [query]


# 模块级单例
query_rewriter = QueryRewriter()
query_expander = QueryExpander()
