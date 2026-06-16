"""查询改写：口语化 → 正式检索词"""
from config.llm import llm_no_stream
from config.logger import logger
from config.prompts import REWRITE_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage


class QueryRewriter:
    """查询改写器：将口语化问题转为正式检索词"""

    def rewrite(self, query: str) -> str:
        """改写查询

        Args:
            query: 原始查询

        Returns:
            改写后的查询，如果改写失败返回原始查询
        """
        try:
            response = llm_no_stream.invoke([
                SystemMessage(content=REWRITE_PROMPT),
                HumanMessage(content=query),
            ])
            # 当前模型只返 str,type: ignore 抑制 Pylance 警告(类型声明是 str | list)
            rewritten = response.content.strip()  # type: ignore

            if not rewritten or len(rewritten) > len(query) * 3:
                logger.warning(f"查询改写结果异常，使用原始查询: {rewritten}")
                return query

            logger.info(f"查询改写: {query} → {rewritten}")
            return rewritten

        except Exception as e:
            logger.error(f"查询改写失败: {e}")
            return query


# 模块级单例
queryRewriter = QueryRewriter()
