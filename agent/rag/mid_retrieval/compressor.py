"""上下文压缩：提取文档中与问题相关的片段"""
from pydantic import SecretStr
from langchain_core.documents import Document
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


class ContextCompressor:
    """上下文压缩器：从文档中提取与查询相关的片段"""

    def __init__(self):
        """初始化压缩器，使用 LLM 进行相关性判断"""
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=SecretStr(settings.llm_api_key),
            base_url=settings.llm_base_url,
            temperature=0,
        )

    def compress(self, query: str, documents: list[Document]) -> list[Document]:
        """
        压缩文档，保留与查询相关的片段。
        @param query: 查询文本
        @param documents: 文档列表
        @return: 压缩后的文档列表
        """
        if not documents:
            return []

        compressed_docs = []
        for doc in documents:
            # 构建压缩提示词
            prompt = f"""请从以下文档中提取与查询相关的片段，保留原文，不要修改。
如果文档与查询无关，返回空字符串。

查询：{query}

文档：{doc.page_content}

相关片段："""

            # 调用 LLM 提取相关片段
            response = self._llm.invoke(prompt)
            content = _parse_content(response.content).strip()

            if content:
                compressed_doc = Document(
                    page_content=content,
                    metadata={**doc.metadata, "original_length": len(doc.page_content)},
                )
                compressed_docs.append(compressed_doc)

        return compressed_docs

    async def acompress(self, query: str, documents: list[Document]) -> list[Document]:
        """
        异步压缩文档。
        @param query: 查询文本
        @param documents: 文档列表
        @return: 压缩后的文档列表
        """
        if not documents:
            return []

        compressed_docs = []
        for doc in documents:
            prompt = f"""请从以下文档中提取与查询相关的片段，保留原文，不要修改。
如果文档与查询无关，返回空字符串。

查询：{query}

文档：{doc.page_content}

相关片段："""

            response = await self._llm.ainvoke(prompt)
            content = _parse_content(response.content).strip()

            if content:
                compressed_doc = Document(
                    page_content=content,
                    metadata={**doc.metadata, "original_length": len(doc.page_content)},
                )
                compressed_docs.append(compressed_doc)

        return compressed_docs


# 模块级单例
compressor = ContextCompressor()
