"""查询扩展：生成多个语义相关查询，扩大召回"""
from config.llm import llm_no_stream
from config.logger import logger
from agent.prompts import EXPANSION_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage


class QueryExpander:
    """查询扩展器：将一个查询扩展为多个语义相关查询"""

    def expand(self, query: str, count: int = 3) -> list[str]:
        """
        扩展查询。
        @param query: 原始查询（通常是改写后的）
        @param count: 扩展数量
        @return: 扩展后的查询列表（包含原始查询）
        """
        try:
            # 一、调用 LLM 扩展
            prompt = EXPANSION_PROMPT.format(count=count)
            response = llm_no_stream.invoke([
                SystemMessage(content=prompt),
                HumanMessage(content=query),
            ])

            # 二、解析结果
            expanded = [
                line.strip()
                for line in response.content.strip().split("\n")
                if line.strip() and line.strip() != query
            ]

            # 三、校验结果
            if not expanded:
                logger.warning("查询扩展结果为空，使用原始查询")
                return [query]

            # 四、合并：原始查询 + 扩展查询
            result = [query] + expanded[:count]
            logger.info(f"查询扩展: 1 → {len(result)} 个")
            return result

        except Exception as e:
            logger.error(f"查询扩展失败: {e}")
            return [query]


# 模块级单例
query_expander = QueryExpander()
