"""嵌入模型封装：统一接口，支持通义千问、OpenAI等"""
from pydantic import SecretStr
from langchain_openai import OpenAIEmbeddings
from config.settings import settings


class EmbeddingFactory:
    """嵌入模型工厂：根据配置创建嵌入模型实例"""

    @staticmethod
    def create() -> OpenAIEmbeddings:
        """
        创建嵌入模型实例。
        @return: OpenAIEmbeddings 实例（兼容通义千问接口）
        """
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=SecretStr(settings.embedding_api_key),
            base_url=settings.embedding_base_url,
        )


# 模块级单例
embeddings = EmbeddingFactory.create()
