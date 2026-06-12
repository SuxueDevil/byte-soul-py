"""HyDE (Hypothetical Document Embeddings)：生成假设性文档嵌入"""
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


class HyDEGenerator:
    """HyDE 生成器：让 LLM 生成假设性答案，用答案做向量检索"""

    def __init__(self):
        """初始化 HyDE 生成器"""
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=SecretStr(settings.llm_api_key),
            base_url=settings.llm_base_url,
            temperature=0.7,
        )
        self._prompt = """请根据以下问题生成一个假设性的答案段落。
这个答案不需要是正确的，但应该看起来像是一个真实的文档片段。

要求：
1. 使用正式的文档语言
2. 包含与问题相关的专业术语
3. 长度约 100-200 字
4. 只输出答案段落，不要输出其他内容

问题：{query}

假设性答案："""

    def generate(self, query: str) -> str:
        """
        生成假设性文档。
        @param query: 查询文本
        @return: 假设性文档内容
        """
        response = self._llm.invoke(self._prompt.format(query=query))
        return _parse_content(response.content).strip()

    async def agenerate(self, query: str) -> str:
        """
        异步生成假设性文档。
        @param query: 查询文本
        @return: 假设性文档内容
        """
        response = await self._llm.ainvoke(self._prompt.format(query=query))
        return _parse_content(response.content).strip()


# 模块级单例
hyde_generator = HyDEGenerator()
