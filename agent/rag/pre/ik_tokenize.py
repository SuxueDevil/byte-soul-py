"""IK 分词：提取用户查询中的关键词，辅助 LLM 改写"""
import jieba
from config.logger import logger


class IKTokenizer:
    """IK 分词器：提取关键词，辅助 LLM 改写"""

    def extract_keywords(self, query: str) -> list[str]:
        """提取关键词

        Args:
            query: 用户原始查询

        Returns:
            关键词列表
        """
        # 一、jieba 分词
        words = jieba.cut(query)
        # 二、过滤停用词和短词
        keywords = [w.strip() for w in words if len(w.strip()) > 1]
        logger.info(f"[IKTokenizer] 分词: {query} → {keywords}")
        return keywords


ikTokenizer = IKTokenizer()
