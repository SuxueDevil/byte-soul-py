"""Product 服务层：调用 Java 后端 API 获取推荐数据"""
import httpx
import random
from config.settings import settings


class ProductService:

    @staticmethod
    def recommend():
        """
        同步获取推荐商品列表，随机返回最多 3 个。
        @return: 随机抽取的商品列表
        """
        data = httpx.get(url=f"{settings.java_url}/api/recommend").json()
        return random.sample(data, min(3, len(data)))

    @staticmethod
    async def recommend_async(method: str, path: str, body: dict = None) -> dict:
        """
        异步调用 Java 后端通用接口。
        @param method: HTTP 方法（GET/POST/PUT/DELETE）
        @param path: 接口路径，如 /api/recommend
        @param body: 请求体 JSON，可选
        @return: 接口响应的 JSON dict
        """
        async with httpx.AsyncClient() as client:
            return await client.request(method, f"{settings.java_url}{path}", json=body).json()
