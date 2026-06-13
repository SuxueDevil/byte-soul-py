"""嵌入模型封装：通义千问 text-embedding-v3"""
from openai import OpenAI
from config.settings import settings
from config.logger import logger


class EmbeddingModel:
    """嵌入模型：封装通义千问 text-embedding-v3，提供统一接口"""

    def __init__(self):
        # 一、创建 OpenAI 兼容客户端
        # 1、通义千问 embedding API 兼容 OpenAI 接口
        self._client = OpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )
        self._model = settings.embedding_model
        self._dimensions = settings.embedding_dimensions

    def embed_query(self, text: str) -> list[float]:
        """
        将单条文本转为向量。
        @param text: 输入文本
        @return: 向量列表（1024 维）
        """
        response = self._client.embeddings.create(
            model=self._model,
            input=text,
            dimensions=self._dimensions,
        )
        return response.data[0].embedding

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        批量将文本转为向量。
        @param texts: 文本列表
        @return: 向量列表
        """
        if not texts:
            return []

        # 一、批量调用 embedding API
        # 1、DashScope 单次最多支持 25 条，分批处理
        all_embeddings = []
        batch_size = 25
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
                dimensions=self._dimensions,
            )
            all_embeddings.extend([item.embedding for item in response.data])

        logger.info(f"嵌入完成: {len(texts)} 条文本, 维度 {self._dimensions}")
        return all_embeddings


# 模块级单例
embedding_model = EmbeddingModel()
